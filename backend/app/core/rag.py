from sentence_transformers import SentenceTransformer

class EmbeddingEngine:
    def __init__(self):
        # We use "all-MiniLM-L6-v2". It's small, fast, and very accurate.
        # It maps sentences to a 384-dimensional dense vector space.
        print("--- RAG: Loading AI Model (this happens once)... ---")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("--- RAG: Model Loaded. ---")

    def generate_embedding(self, text: str) -> list[float]:
        """
        Converts text into a list of floating point numbers (Vector).
        """
        # The model expects a list of sentences, but we can pass a single string.
        # .tolist() converts the numpy array to a standard Python list.
        embedding = self.model.encode(text).tolist()
        return embedding

# Create a singleton instance
embedding_engine = EmbeddingEngine()