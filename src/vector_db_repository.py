import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = "http://localhost:6333"

class VectorDBRepository:
    def __init__(self, collection_name: str):
        self.client = QdrantClient(url=QDRANT_URL)
        self.collection_name = collection_name


    def collection_exists(self):
        return self.client.collection_exists(collection_name=self.collection_name)
    
    def create_collection(self):
        if self.client.collection_exists(collection_name=self.collection_name):
            return
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                "size": 384,
                "distance": "Cosine"
            }
        )

    def delete_collection(self):
        self.client.delete_collection(
            collection_name=self.collection_name
        )

    def add_document(self, document_id: int, vector: list, payload: dict = {}):
        assert isinstance(payload, dict), "Payload must be a dictionary"
        self.client.upsert(
            collection_name=self.collection_name,
            points=[{
                "id": document_id,
                "vector": vector,
                "payload": {k: v for k, v in payload.items() if v is not None}
            }]
        )

    def search(self, vector: list, limit: int = 5):
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit
        )
        return results
    
# vdb = VectorDBRepository("emails")
# vdb.create_collection()
# print(vdb.collection_exists())
# vdb.delete_collection()