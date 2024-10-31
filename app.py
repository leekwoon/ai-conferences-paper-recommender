import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import tiktoken  # 토큰 계산을 위한 tiktoken 라이브러리

from langchain_community.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings

from constants import OPENAI_EMBEDDING_MODEL_NAME, COST_PER_TOKEN, CHROMA_DB_DIR

openai_api_key = os.getenv("OPENAI_API_KEY")

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def count_tokens(text):
    tokenizer = tiktoken.encoding_for_model(OPENAI_EMBEDDING_MODEL_NAME)
    tokens = tokenizer.encode(text)
    return len(tokens)


# Initialize FastAPI app
app = FastAPI()
# app = FastAPI(
#     servers=[
#         {
#             "url": "https://leekwoon-ai-conferences-paper-recommender.hf.space",
#         }
#     ],
# )

# OpenAI embeddings을 사용하여 벡터 생성
embeddings = OpenAIEmbeddings(
    openai_api_key=openai_api_key,
    model=OPENAI_EMBEDDING_MODEL_NAME
)


@app.post("/search-papers")
def search_papers(
    query: str, 
    conference: str = 'NeurIPS', 
    year: int = 2024, 
    recall_top_k: int = 10,  
):
    """
    API to search for papers by conference and year and return top K results.

    This API allows users to input a query (e.g., the abstract or title of a paper) 
    and search for similar papers from the provided conference and year. 
    The API searches through a collection of papers and returns the most relevant 
    papers based on the given query.

    Supported Conferences and Years:
    - AAAI: 2018 ~ 2024
    - CVPR: 2021 ~ 2024
    - ECCV: 2018, 2020, 2022, 2024
    - EMNLP: 2018 ~ 2023
    - ICCV: 2021, 2023
    - ICLR: 2018, 2019, 2021, 2022, 2023, 2024
    - ICML: 2018 ~ 2024
    - ICRA: 2018 ~ 2024
    - IJCAI: 2018 ~ 2024
    - Interspeech: 2018 ~ 2024
    - ISMIR: 2021 ~ 2023
    - NeurIPS: 2018 ~ 2024

    Parameters:
    - query (str): The search query, typically an abstract or title of a paper.
    - conference (str): The name of the conference. Must be one of the supported conferences.
    - year (int): The year of the conference. Must be one of the supported years.
    - recall_top_k (int, optional): The number of top results to return. 

    Example Usage:
    You can use this API to find similar papers by providing the abstract or key concepts
    of a research paper. For example, if you input the abstract of a paper about "image synthesis 
    evaluation metrics," the API will return the most relevant papers from the specified conference and year.

    Example Query:
    ```
    {
        "query": "Generative models, especially in image synthesis tasks, often require reliable evaluation metrics to measure their performance. While image fidelity is a widely used metric, the diversity of generated images is equally important but often overlooked. In this query, we explore a new evaluation metric, called 'rarity score', which is designed to quantify both the uncommonness of each image and the diversity of images generated by the model. The rarity score is computed based on the distances between generated images in the latent space using feature extractor networks like VGG16. With this metric, one can filter typical and distinctive samples and compare the rarity of images generated by different models or datasets, such as CelebA-HQ and FFHQ. We also aim to understand the relationship between feature space design and high-rarity images, providing a new perspective on generative model performance evaluation.",
        "conference": "NeurIPS",
        "year": 2024,
        "recall_top_k": 10
    }
    ```

    Expected Response:
    The API returns a JSON object with the following fields:
    - total_tokens_used (int): The total number of tokens used in the query.
    - cost (float): The cost associated with embedding the query.
    - results (list of dict): A list of papers and their metadata, including:
        - title (str): The title of the paper.
        - authors (str): The authors of the paper.
        - abstract (str): The abstract of the paper.
        - score (float): The relevance score of the paper.

    Example Response:
    ```
    {
        "total_tokens_used": 168,
        "cost": 0.00000336,
        "results": [
            {
                "title": "Towards a Scalable Reference-Free Evaluation of Generative Models",
                "authors": "Author A, Author B",
                "abstract": "While standard evaluation scores for generative models are ...",
                "score": 0.62,
            },
            {
                "title": "GenAI Arena: An Open Evaluation Platform for Generative Models",
                "authors": "Author C, Author D",
                "abstract": "Generative AI has made remarkable strides to revolutionize fields ...",
                "score": 0.55,
            },
            ...
        ]
    }
    ```

    This API is useful for researchers and developers who want to find relevant academic 
    papers based on a given abstract or paper description.
    """

    try:
        # 학회와 연도에 맞게 다른 collection_name 사용
        collection_name = f"{conference}_{year}_collection"
        
        # Chroma 벡터 스토어 생성 (학회와 연도별로 컬렉션 이름을 다르게 함)
        chroma_vector = Chroma(
            collection_name=collection_name,  # 학회와 연도에 맞는 컬렉션
            embedding_function=embeddings,
            persist_directory=CHROMA_DB_DIR,
            collection_metadata={"hnsw:space": "cosine"}
        )

        # 쿼리의 토큰 수 계산
        tokens_used = count_tokens(query)

        # 쿼리의 토큰 길이 제한 (최대 30,000 토큰까지만 허용)
        max_tokens_limit = 30000
        if tokens_used > max_tokens_limit:
            return JSONResponse(
                status_code=400, 
                content={"message": f"Query exceeds the maximum token limit of {max_tokens_limit}. Your query contains {tokens_used} tokens."}
            )

        # 비용 계산 (text-embedding-3-large의 경우 1M 토큰당 $0.130)
        total_cost = tokens_used * COST_PER_TOKEN

        # 토큰 수와 비용 출력
        logging.info(f"Tokens used for query: {tokens_used}")
        logging.info(f"Cost for embedding the query: ${total_cost:.6f}")

        # 유사도 검색 작업 (필터 추가)
        results = chroma_vector.similarity_search_with_relevance_scores(
            query=query,
            k=recall_top_k
        )

        # 결과가 있는지 확인
        if not results:
            logging.info(f"No results found for source file: {conference}_{year}.json")
            return JSONResponse(status_code=404, content={"message": f"No results found for {conference} {year}."})

        # 결과를 dict로 변환하여 반환 (title, authors, abstract 분리)
        papers = []
        for result, score in results:
            # 페이지 내용을 파싱하여 title, authors, abstract를 추출
            content_lines = result.page_content.split("\n")
            title = content_lines[0].replace("Title: ", "")
            authors = content_lines[1].replace("Authors: ", "")
            abstract = content_lines[2].replace("Abstract: ", "")
            
            papers.append({
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "score": score,
            })

        return {"total_tokens_used": tokens_used, "cost": total_cost, "results": papers}

    except Exception as e:
        # Raise an HTTP 500 error if something goes wrong
        logging.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
