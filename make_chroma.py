import os
import json
import glob
import asyncio
import tiktoken  # OpenAI 토큰화를 위한 라이브러리

from langchain.schema.document import Document
from langchain_community.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings

from constants import OPENAI_EMBEDDING_MODEL_NAME, COST_PER_TOKEN


openai_api_key = os.getenv("OPENAI_API_KEY")


# tiktoken을 사용하여 텍스트를 토큰화하고 토큰 수를 계산
def count_tokens(text):
    tokenizer = tiktoken.encoding_for_model(OPENAI_EMBEDDING_MODEL_NAME)
    tokens = tokenizer.encode(text)
    return len(tokens)

# 비동기적으로 문서 배치를 처리
async def process_batch(batch, chroma_vector, total_tokens):
    await chroma_vector.aadd_documents(batch)
    
    # 배치의 모든 문서에 대해 토큰 수를 계산하고 누적
    batch_tokens = sum(count_tokens(doc.page_content) for doc in batch)
    total_tokens.append(batch_tokens)

def json2documents(input_json):
    source_file_name = os.path.basename(input_json)
    conference_name = source_file_name.split('_')[0]  # 학회명 예: 'NeurIPS'
    year = source_file_name.split('_')[1].replace('.json', '')  # 년도 예: '2023'

    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    documents = []
    for entry in data:
        title = entry.get('title', None)
        authors = entry.get('authors', None)
        abstract = entry.get('abstract', None)

        # title, authors, abstract가 하나라도 없으면 해당 entry를 건너뛰기
        if not title or not authors or not abstract:
            print(f"Warning: Skipping entry due to missing title, authors, or abstract: {entry}")
            continue

        title = title.strip()
        authors = authors.strip()
        abstract = abstract.strip()

        page_content = f"Title: {title}\nAuthors: {authors}\nAbstract: {abstract}"
        metadata = {
            "title": title,
            "authors": authors,
            "source_file": source_file_name,
            "conference": conference_name,
            "year": year 
        }
        doc = Document(page_content=page_content, metadata=metadata)
        documents.append(doc)
    return documents


async def main():
    # OpenAI embeddings을 사용하여 벡터 생성
    embeddings = OpenAIEmbeddings(
        openai_api_key=openai_api_key,
        model=OPENAI_EMBEDDING_MODEL_NAME
    )

    input_jsons = glob.glob('./data/*.json')
    # 파일명에서 년도가 2018 ~ 2024인 항목만 추출
    input_jsons = [file for file in input_jsons if any(year in file for year in ['2018', '2019', '2020', '2021', '2022', '2023', '2024'])]

    for input_json in input_jsons:
        print(input_json)
        documents_to_add = json2documents(input_json)

        if len(documents_to_add) == 0:
            print(f"pass as collection '{collection_name}' as it is empty.")
            continue  # 이미 데이터가 있는 경우 넘어감

        # 학회와 연도에 맞게 다른 collection_name 사용
        conference_name = documents_to_add[0].metadata["conference"]
        year = documents_to_add[0].metadata["year"]
        collection_name = f"{conference_name}_{year}_collection"
        
        # Chroma 벡터 스토어 생성 (학회와 연도별로 컬렉션 이름을 다르게 함)
        chroma_vector = Chroma(
            collection_name=collection_name,  # 학회와 연도에 맞는 컬렉션
            embedding_function=embeddings,
            persist_directory='chroma_dir',
            collection_metadata={"hnsw:space": "cosine"}
        )

        # 컬렉션의 데이터 개수 확인
        try:
            existing_collection = chroma_vector._client.get_collection(collection_name)
            doc_count = existing_collection.count()

            if doc_count == len(documents_to_add):
                print(f"pass as collection '{collection_name}' already has {doc_count} documents.")
                continue  # 이미 데이터가 있는 경우 넘어감

        except Exception as e:
            print(f"Error retrieving collection: {e}. Proceeding to add data...")

        # Chroma에 문서 추가 (병렬 처리)
        ADD_BATCH_SIZE = 120
        total_tokens = []  # 사용된 토큰 수를 추적하기 위한 리스트

        tasks = []
        for start in range(0, len(documents_to_add), ADD_BATCH_SIZE):
            print(f"Processing batch starting at index {start}")
            batch = documents_to_add[start:start + ADD_BATCH_SIZE]
            
            # 각 배치를 병렬로 처리하기 위해 task 추가
            tasks.append(process_batch(batch, chroma_vector, total_tokens))

        # 모든 배치들을 병렬로 처리 (await로 전체 작업이 끝날 때까지 기다림)
        await asyncio.gather(*tasks)

        # 총 사용된 토큰 계산
        total_tokens_used = sum(total_tokens)
        total_cost = total_tokens_used * COST_PER_TOKEN

        print(f"Added {len(documents_to_add)} documents to Chroma.")
        print(f"Total tokens used: {total_tokens_used}")
        print(f"Total cost for this request: ${total_cost:.6f}")


if __name__ == "__main__":
    # asyncio를 사용하여 비동기 main 함수를 실행
    asyncio.run(main())