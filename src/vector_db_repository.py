import os
from datetime import datetime
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Record
from dotenv import load_dotenv

import csv_logging_repository
import mbox_util

load_dotenv()

QDRANT_URL = "http://localhost:6333"

class VectorDBRepository:
    def __init__(self, collection_name: str, batch_size: int = 500):
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
    
    def populate_collection(self):
        """
            Populate the collection with data. This method is a placeholder and should be implemented as needed.
        """
        try:
            # Read previous processing stats from the CSV log
            stats = csv_logging_repository.read_stats()
            if stats:
                processed, skipped = stats
                processed = int(processed)
                skipped = int(skipped)
                print(f"Processed: {processed}, Skipped: {skipped}")
            else:
                processed, skipped = 0, 0
                print("No Previous Uploads Logged")
                
            # Determine the starting point for processing
            start_point = int(processed) + int(skipped)
            print(f"Starting from message index: {start_point}")
            
            # Check if the collection exists and handle accordingly
            if self.collection_exists():
                vdb_count = self.count()
                print(f"Collection already exists with {vdb_count} documents.")
            else:
                self.create_collection()
            
            # Start processing and embedding emails
            start = datetime.now()
            mbox_count = mbox_util.get_mbox_count()
            
            print("Total messages in mbox:", mbox_count)
            if start_point >= mbox_count:
                print("No new messages to process. Start point is greater than or equal to the total message count.")
                return
            
            # Iterate through the emails and process them
            for i in tqdm(range(start_point, mbox_count), desc="Embedding Email", unit="email"):
                try:
                    metadata, data = mbox_util.extract_metadata(i)        
                    if metadata is None or data is None:
                        print(f"Skipping message {i} due to missing metadata or data.")
                        skipped += 1
                        continue
                    vector = mbox_util.create_vector_embedding(data=data)
                                
                    self.add_document(document_id=i, vector=vector, payload=metadata, skipped_count=skipped)
                    
                except Exception as e:
                    print(f"Error processing message {i}: {e}")
                    return
            # Calculate and display elapsed time
            end = datetime.now()
            elapsed_time = (end - start).total_seconds()
            print(f"Elapsed time: {elapsed_time:.2f} seconds")
        
        except KeyboardInterrupt:
            print("\nProcess interrupted by user.")
        except TimeoutError:
            print("\nProcess timed out.")
        except Exception as e:
            print(f"\nAn error occurred: {e}")
    
    # -----
    # Document Add Management
    # -----

    def add_document(self, document_id: int, vector: list, payload: dict = {}, skipped_count: int = 0):
        """
            Add a document to a buffer.
        """
        assert isinstance(payload, dict), "Payload must be a dictionary"
        assert len(vector) == 384, "Vector must be of length 384"
        
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
    # Vector Retrieval
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
    
    def context_search(self, text: str, limit: int = 5):
        
        text_embedding = mbox_util.create_vector_embedding(data=text)
        
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=text_embedding,
            limit=limit,
            with_payload=True,
        )
        
        return search_result
    
    def get_document(self, document_id: int) -> Record:
        """
            Retrieve a document from the collection.
        """
        result = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[document_id],
            with_vectors=True,
        )
        return result[0]
    


if __name__ == "__main__":
    vdb = VectorDBRepository("emails")
    
    while True:
        print("\nWelcome to the VectorDB handler:")
        print("1. Create Collection")
        print("2. Delete Collection")
        print("3. Check if Collection Exists")
        print("4. Count Documents in Collection")
        print("5. Get Document by ID") 
        print("6. Exit")
        
        choice = input("Enter your choice: ")
        print()
        match choice:
            case "1":                    
                vdb.populate_collection()
                
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
                if not vdb.collection_exists():
                    print("Collection does not exist.")
                    continue
                document_id = int(input("Enter document ID: "))
                document = vdb.get_document(document_id)
                if document:
                    print(f"Document ID: {document.id}")
                    print(f"Document Payload: {document.payload}")
                else:
                    print("Document not found.")
            case "6":
                print("Exiting...")
                break
            case _:
                print("Invalid choice. Please try again.")