import os
import glob
import chromadb
from chromadb.config import Settings

# By default, save ChromaDB locally
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
COLLECTION_NAME = "triagecrew_knowledge"

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        # Using default embedding function (all-MiniLM-L6-v2) for simplicity
        # A production system would inject a specific OpenAI or other embedding function
        self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)
        
    def load_documents(self, docs_dir="app/rag/knowledge_base"):
        """Reads markdown files from docs_dir and loads them into Chroma."""
        # Simple chunking by heading (##)
        count = self.collection.count()
        if count > 0:
            print(f"ChromaDB already has {count} documents. Skipping load.")
            return

        print(f"Loading documents from {docs_dir}...")
        files = glob.glob(f"{docs_dir}/*.md")
        
        docs = []
        metadatas = []
        ids = []
        
        doc_id = 1
        for file_path in files:
            category = os.path.basename(file_path).replace(".md", "")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Split by '## ' for very simple naive chunking
            chunks = content.split("## ")
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                # Add back the '## ' if it's not the first chunk (which might be the title)
                text = f"## {chunk}" if i > 0 else chunk
                docs.append(text.strip())
                metadatas.append({"source": category, "chunk_index": i})
                ids.append(f"doc_{doc_id}")
                doc_id += 1
                
        if docs:
            self.collection.add(
                documents=docs,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Loaded {len(docs)} chunks into ChromaDB.")

    def retrieve(self, query: str, top_k: int = 3):
        """Returns top_k most similar chunks to the query."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        retrieved_chunks = []
        # Results format: {'ids': [[...]], 'distances': [[...]], 'metadatas': [[...]], 'documents': [[...]]}
        if not results['documents'] or not results['documents'][0]:
            return []
            
        for i in range(len(results['documents'][0])):
            doc_text = results['documents'][0][i]
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i] if 'distances' in results and results['distances'] else 0.0
            
            # Convert distance to a pseudo similarity score (1 - distance) if cosine/l2
            # ChromaDB default is L2 distance, lower is better. 
            # We'll invert it roughly. If it's too high, score is low.
            score = max(0.0, 1.0 - (distance / 2.0))
            
            retrieved_chunks.append({
                "text": doc_text,
                "source": metadata.get("source", "unknown"),
                "score": score
            })
            
        return retrieved_chunks

# Singleton instance
vector_store = VectorStore()

# The tool function that will be wrapped for CrewAI
def chroma_retriever_tool(query: str, top_k: int = 3) -> list:
    """
    Search the knowledge base for policy and FAQ documents relevant to the ticket.
    Returns a list of dictionaries with text, source, and score.
    """
    return vector_store.retrieve(query, top_k)
