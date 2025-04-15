import os
from tqdm import tqdm
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from datetime import datetime
from vector_db_repository import VectorDBRepository
import csv_logging_repository
import mbox_util

load_dotenv()

if __name__ == "__main__":


    vector_db = VectorDBRepository(
        collection_name="emails",
        batch_size=1000
    )
    
    text = input("Query the DB: ")

    start_time = datetime.now()
    out = vector_db.context_search(text=text, limit=10)
    print(len(out))
    for i, item in enumerate( out):
        
        print(f"{i+1}: {item.id}, {item.score}", 
              "\nsubject:", item.payload["subject"],
              "\nfrom:", item.payload["from"],
              "\nDate:", item.payload["date"],)
        print()
        
        
    end_time = datetime.now()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time.total_seconds()}s")

    pass