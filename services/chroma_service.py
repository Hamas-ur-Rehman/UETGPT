import os
import time
import shutil
from tqdm import tqdm
from dotenv import load_dotenv
from utils.custom_logger import log
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders.csv_loader import CSVLoader
import threading
from concurrent.futures import ThreadPoolExecutor
load_dotenv()


class ChromaService:
    def loader(self):
        try:
            start_time = time.time()
            
            # Initialize the embeddings function from OpenAI
            embeddings = OpenAIEmbeddings()

            # Initialize the Chroma vector store
            log.info("Initializing Chroma vector store")
            if os.path.exists("./chromadb"):
                log.info("Removing existing Chroma vector store")
                shutil.rmtree("./chromadb")
            vectorstore = Chroma(
                persist_directory="./chromadb",
                embedding_function=embeddings,
                collection_name="properties"
            )

            # Load the data from the CSV file
            log.info("Loading data from CSV file")
            loader = CSVLoader(file_path="./dataset/property.csv")
            data = loader.load()

            # Function to add texts to the Chroma vector store in batches
            def add_text_batch(batch):
                try:
                    texts = [record.page_content for record in batch]
                    Chroma.add_texts(vectorstore, texts)
                except Exception as e:
                    log.error(f"Error adding text batch to vector store: {e}", exc_info=True)

            # Define batch size
            batch_size = 100  # You can adjust the batch size for optimal performance

            # Create batches of records
            batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]

            # Load the data into the Chroma vector store using a thread pool
            log.info(f"Loading data into Chroma vector store in batches. Total records: {len(data)}, Total batches: {len(batches)}")
            with ThreadPoolExecutor(max_workers=10) as executor:
                list(tqdm(executor.map(add_text_batch, batches), total=len(batches)))

            log.info("Data loaded successfully")
            log.warning(f"Time taken to load data: {round(time.time() - start_time, 2)} seconds")
        except Exception as e:
            log.error(f"Error in loader: {e}", exc_info=True)

    def retriver(self, question, k=4):
        try:
            start_time = time.time()
            # Initialize the embeddings function from OpenAI
            embeddings = OpenAIEmbeddings()
            vectorstore = Chroma(
                persist_directory="./chromadb",
                embedding_function=embeddings,
                collection_name="properties"
                )
            log.info("Retrieving documents from Chroma vector store")
            DOCS = []
            for i in vectorstore.similarity_search(question, k=k):
                DOCS.append(i.page_content)
            if len(DOCS) == 0:
                DOCS.append("Sorry, I couldn't find any relevant documents")
            log.warning(f"Time taken to retrieve documents: {round(time.time() - start_time,2)} seconds")
            return DOCS
        except Exception as e:
            log.error(f"Error in retriver: {e}", exc_info=True)
            return ["Sorry, I couldn't find any relevant documents"]
