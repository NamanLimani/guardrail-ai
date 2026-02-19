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
import time

class EmbeddingEngine:
    def __init__(self):
        self.hf_token = os.getenv("HF_TOKEN")
        # Use the specific feature-extraction task URL to get vectors
        self.api_url = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2"
        self.headers = {"Authorization": f"Bearer {self.hf_token}"}
        print("--- RAG: Configured for Hugging Face Cloud Inference ---")

    def generate_embedding(self, text: str) -> list[float]:
        if not self.hf_token:
            return [0.0] * 384

        # The new router for this specific model expects raw text in 'inputs'
        payload = {"inputs": text}

        try:
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                json=payload,
                timeout=15
            )
            
            # If the model is still "loading" on Hugging Face's side
            if response.status_code == 503:
                print("RAG: Model is loading, waiting 5s...")
                time.sleep(5)
                return self.generate_embedding(text)

            if response.status_code == 200:
                result = response.json()
                # Feature extraction returns a list of floats
                return result
            else:
                print(f"RAG API Error ({response.status_code}): {response.text}")
                return [0.0] * 384
                
        except Exception as e:
            print(f"RAG Request Failed: {e}")
            return [0.0] * 384

embedding_engine = EmbeddingEngine()