# from sentence_transformers import SentenceTransformer

# class EmbeddingEngine:
#     def __init__(self):
#         # We use "all-MiniLM-L6-v2". It's small, fast, and very accurate.
#         # It maps sentences to a 384-dimensional dense vector space.
#         print("--- RAG: Loading AI Model (this happens once)... ---")
#         self.model = SentenceTransformer('all-MiniLM-L6-v2')
#         print("--- RAG: Model Loaded. ---")

#     def generate_embedding(self, text: str) -> list[float]:
#         """
#         Converts text into a list of floating point numbers (Vector).
#         """
#         # The model expects a list of sentences, but we can pass a single string.
#         # .tolist() converts the numpy array to a standard Python list.
#         embedding = self.model.encode(text).tolist()
#         return embedding

# # Create a singleton instance
# embedding_engine = EmbeddingEngine()


import os
import requests

class EmbeddingEngine:
    def __init__(self):
        # We grab the token from the Environment (Render/Local)
        self.hf_token = os.getenv("HF_TOKEN")
        # The specific Hugging Face URL for our chosen embedding model
        self.api_url = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2"
        self.headers = {"Authorization": f"Bearer {self.hf_token}"}
        print("--- RAG: Configured for Hugging Face Cloud Inference ---")

    def generate_embedding(self, text: str) -> list[float]:
        """
        Sends text to Hugging Face and returns the 384-dimensional vector.
        """
        if not self.hf_token:
            print("WARNING: HF_TOKEN is missing! Vector search will fail.")
            return [0.0] * 384

        try:
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                json={"inputs": text},
                timeout=10 # 10 second timeout so we don't hang forever
            )
            
            if response.status_code == 200:
                # The API returns the exact array of floats we need
                return response.json()
            else:
                print(f"RAG API Error ({response.status_code}): {response.text}")
                return [0.0] * 384
                
        except Exception as e:
            print(f"RAG Request Failed: {e}")
            return [0.0] * 384

# Create a singleton instance
embedding_engine = EmbeddingEngine()