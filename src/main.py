import os
from tqdm import tqdm
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from datetime import datetime
import vector_db_repository
import mbox_util

load_dotenv()


def populate_vector_collection():
    start = datetime.now()
    count = mbox_util.get_mbox_count()
    print("Total messages in mbox:", count)
    
    vector_db = vector_db_repository.VectorDBRepository(collection_name="emails")    

    if vector_db.collection_exists():
        print("Collection already exists. Deleting.")
        vector_db.delete_collection()
 
    
    vector_db.create_collection()

    for i in tqdm(range(count), desc="Embedding Email", unit="email"):
        try:
            
            metadata, data = mbox_util.extract_metadata(i)        
            if metadata is None or data is None:
                print(f"Skipping message {i} due to missing metadata or data.")
                continue
            vector = mbox_util.create_vector_embedding(data=data)
                        
            vector_db.add_document(document_id=i, vector=vector, payload=metadata)
            
    
        except Exception as e:
            print(f"Error processing message {i}: {e}")
            return


    end = datetime.now()
    elapsed_time = end - start
    print(f"Elapsed time: {elapsed_time.total_seconds()}s")
    
if __name__ == "__main__":
    populate_vector_collection()
    
