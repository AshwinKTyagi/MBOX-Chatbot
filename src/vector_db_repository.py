import os
from datetime import datetime
from tqdm import tqdm
from qdrant_client import QdrantClient
from dotenv import load_dotenv

import csv_logging_repository
import mbox_util

load_dotenv()

QDRANT_URL = "http://localhost:6333"

class VectorDBRepository:
    def __init__(self, collection_name: str, batch_size: int = 1000):
        self.client = QdrantClient(url=QDRANT_URL)
        self.collection_name = collection_name
        self.batch_size = batch_size
        self._buffer = []


    # -----
    # Collection Management
    # -----
    
    def create_collection(self) -> bool:
        """
            Create a collection in the database if it does not already exist. 
        """
        if self.client.collection_exists(collection_name=self.collection_name):
            return False
        
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                "size": 384,
                "distance": "Cosine"
            }
        )
        return True

    def delete_collection(self):
        """
            Delete the collection from the database.
        """
        csv_logging_repository.update_csv(
            processed_increment=0,
            skipped_increment=0
        )
        self.client.delete_collection(
            collection_name=self.collection_name
        )
        
    def collection_exists(self) -> bool:
        """
            Check if the collection exists.        
        """
        return self.client.collection_exists(collection_name=self.collection_name)
    
    def count(self) -> int:
        """
            Count the number of documents in the collection.
        """
        return self.client.count(collection_name=self.collection_name).count
    
    def populate_collection(self, start_point: int = 0, skipped_count: int = 0):
        """
            Populate the collection with data. This method is a placeholder and should be implemented as needed.
        """
        try:
            stats = csv_logging_repository.read_stats()
            if stats:
                processed, skipped = stats
                total = int(processed) + int(skipped)
                print(f"Processed: {processed}, Skipped: {skipped}")
            else:
                processed, skipped = 0, 0
                print("No Previous Uploads Logged")
                
            start_point = int(processed) + int(skipped)
            print(f"Start Point: {start_point}\n")
            custom_start = input("Enter custom start point (or press Enter to use default): ")
            if custom_start:
                start_point = int(custom_start)
                print(f"Custom Start Point: {start_point}")
                
            if self.collection_exists():
                vdb_count = self.count()
                print(f"Collection already exists with {vdb_count} documents.")
                return
            
            start = datetime.now()
            mbox_count = mbox_util.get_mbox_count()
            
            print("Total messages in mbox:", mbox_count)
            self.create_collection()
            for i in tqdm(range(start_point, mbox_count), desc="Embedding Email", unit="email"):
                try:
                    metadata, data = mbox_util.extract_metadata(i)        
                    if metadata is None or data is None:
                        print(f"Skipping message {i} due to missing metadata or data.")
                        skipped_count += 1
                        continue
                    vector = mbox_util.create_vector_embedding(data=data)
                                
                    self.add_document(document_id=i, vector=vector, payload=metadata, skipped_count=skipped_count)
                    
                except Exception as e:
                    print(f"Error processing message {i}: {e}")
                    return
            end = datetime.now()
            elapsed_time = end - start
            print(f"Elapsed time: {elapsed_time}s")
        
        except KeyboardInterrupt:
            print("\nProcess interrupted by user.")
        except TimeoutError:
            print("\nProcess timed out.")
        except Exception as e:
            print(f"\nAn error occurred: {e}")

    
    
    
    # -----
    # Document Management
    # -----

    def add_document(self, document_id: int, vector: list, payload: dict = {}, skipped_count: int = 0):
        """
            Add a document to a buffer.
        """
        assert isinstance(payload, dict), "Payload must be a dictionary"
        
        self._buffer.append({
            "id": document_id,
            "vector": vector,
            "payload": {k: v for k, v in payload.items() if v is not None}
        })
        
        if len(self._buffer) >= self.batch_size:
            self.flush(skipped_count)

    def flush(self, skipped_count: int):
        """
            Flush the buffer to the database.
        """
        if not self._buffer:
            return

        csv_logging_repository.update_csv(
            processed_increment=len(self._buffer) + self.count(),
            skipped_increment=skipped_count
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=self._buffer
        )
        self._buffer.clear()

    # ----
    # Search
    # ----


    def search(self, vector: list, limit: int = 5):
        """
            Search for similar documents in the collection.
        """
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit
        )
        return results
    


if __name__ == "__main__":
    vdb = VectorDBRepository("emails")
    
    while True:
        print("\nWelcome to the VectorDB handler:")
        print("1. Create Collection")
        print("2. Delete Collection")
        print("3. Check if Collection Exists")
        print("4. Count Documents in Collection")
        print("5. Exit")
        
        choice = input("Enter your choice: ")
        print()
        match choice:
            case "1":
                if vdb.create_collection():
                    print("Collection created successfully.")
                else:
                    print("Collection already exists.")
            case "2":
                vdb.delete_collection()
                print("Collection deleted successfully.")
            case "3":
                if vdb.collection_exists():
                    print("Collection exists.")
                else:
                    print("Collection does not exist.")
            case "4":
                if not vdb.collection_exists():
                    print("Collection does not exist.")
                    continue
                print(f"Number of documents in collection: {int(vdb.count())}")
            case "5":
                print("Exiting...")
                break
            case _:
                print("Invalid choice. Please try again.")