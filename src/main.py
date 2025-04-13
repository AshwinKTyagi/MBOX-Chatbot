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


def populate_vector_collection(vector_db: VectorDBRepository, start_point: int = 0, skipped_count: int = 0):
    """
        Populate the vector collection with email data.
    """
    start = datetime.now()
    mbox_count = mbox_util.get_mbox_count()
    
    print("Total messages in mbox:", mbox_count)
    
    vector_db.create_collection()

    for i in tqdm(range(start_point, mbox_count), desc="Embedding Email", unit="email"):
        try:
            
            metadata, data = mbox_util.extract_metadata(i)        
            if metadata is None or data is None:
                print(f"Skipping message {i} due to missing metadata or data.")
                skipped_count += 1
                continue
            vector = mbox_util.create_vector_embedding(data=data)
                        
            vector_db.add_document(document_id=i, vector=vector, payload=metadata, skipped_count=skipped_count)
            
    
        except Exception as e:
            print(f"Error processing message {i}: {e}")
            return


    end = datetime.now()
    elapsed_time = end - start
    print(f"Elapsed time: {elapsed_time.total_seconds()}s")
    
if __name__ == "__main__":
    try:
        batch_size = 100
        vector_db = VectorDBRepository(collection_name="emails", batch_size=batch_size)
        
        stats = csv_logging_repository.read_stats()
        if stats:
            processed, skipped = stats
            total = int(processed) + int(skipped)
            print(f"Processed: {processed}, Skipped: {skipped}")
        else:
            processed, skipped = 0, 0
            print("No Previous Uploads Logged")
            
        start_point = int(processed) + int(skipped)
        print(f"Start Point: {start_point}")
        custom_start = input("Enter custom start point (or press Enter to use default): ")
        if custom_start:
            start_point = int(custom_start)
            print(f"Custom Start Point: {start_point}")
        
        if vector_db.collection_exists():
            vdb_count = vector_db.count()
            print(f"Collection already exists with {vdb_count} documents.")
            
            
        populate_vector_collection(vector_db=vector_db, start_point=start_point, skipped_count=int(skipped))
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except TimeoutError:
        print("\nProcess timed out.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")