import os
from tqdm import tqdm
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from datetime import datetime
from vector_db_repository import VectorDBRepository
import csv_logging_repository
import mbox_util
import signal


load_dotenv()

def timeout_handler(signum, frame):
    print("Timeout occurred. Exiting.")
    raise TimeoutError("Timeout occurred while processing the email.")

        
if __name__ == "__main__":
    #test search
    pass