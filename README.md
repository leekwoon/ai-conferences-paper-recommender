# ai-conferences-paper-recommender

This repository provides a useful API service for students and researchers to discover relevant papers from top venues based on their input keywords or abstracts (full sentences). You can quickly skim through the abstracts and similarity scores of the search results on this page.

Give it a try! 🔍 [Explore the API](https://leekwoon-ai-conferences-paper-recommender.hf.space/docs#/default/search_papers_search_papers_post) 🔍

## Setup

To get started, set up a dedicated environment and install all necessary dependencies:
```bash
conda create -n acpr anaconda python=3.8
source activate acpr
conda activate acpr

cd ai-conferences-paper-recommender
pip install -r requirements.txt
```

Then, set your OpenAI API key as an environment variable to enable embeddings with OpenAI’s models:

```
export OPENAI_API_KEY=your_openai_api_key_here
```

This API key is necessary for generating embeddings in the `make_chroma.py` script. Replace `your_openai_api_key_here` with your actual OpenAI API key.

## Data Crawling

For example, to crawl paper titles, authors, and abstracts from the CVPR conference, simply run the following command:

```
bash scripts/crawl_CVPR.sh
```

Additionally, pre-crawled data is available in the data folder for easy access.

## Make Chroma Vectors

To process and store the research paper data as vector embeddings, first download the `chroma_dir.zip` file with gdown and `unzip` it:

```
# Download chroma_dir.zip using gdown
gdown https://drive.google.com/uc?id=1CbkQOny-YOqfHVWlPewOaJXDBveTqBzt

# Unzip chroma_dir.zip
unzip chroma_dir.zip
```

This step will create a `chroma_dir` folder with the preprocessed Chroma vectors needed for the paper recommender.

If you want to recreate the Chroma vectors yourself, use the following command to run `make_chroma.py`:

```
python make_chroma.py
```

The `make_chroma.py` script converts the JSON data in the data folder into vector embeddings and saves them in a Chroma vector store. This process includes tokenizing each paper's content and calculating associated token costs.

## Searching Papers

This repository includes a FastAPI-based application located in `app.py`. To run the server, use the command below:

```
uvicorn app:app --host 0.0.0.0 --port 7860
```

Then, you can test the application at [localhost:7860/docs](localhost:7860/docs)

