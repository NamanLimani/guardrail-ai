import os
from groq import Groq
import json

class ChatEngine:
    def __init__(self):
        # 1. Initialize the Groq Client
        # It automatically picks up GROQ_API_KEY from the environment variables
        self.client = Groq()
        # We use Llama3-8b-8192 which is fast and free on Groq
        self.model = "llama-3.3-70b-versatile"


    def generate_streaming_answer(self, query: str, context: str, history: list = [], debug_data: dict = None):
        """
        Yields JSON strings: First the metadata, then the answer chunks.
        """
        try:
            # 1. Send Debug Info FIRST (if available)
            if debug_data:
                yield json.dumps({"type": "debug", "data": debug_data}) + "\n"

            # 2. Setup the AI Request
            system_prompt = (
                "You are GuardRail AI. Use the Context to answer. "
                "If asked for opinions, use general knowledge. "
                "Context contains <REDACTED> tags for safety."
            )

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(history[-4:]) 
            user_message = f"Context:\n{context}\n\nQuestion: {query}"
            messages.append({"role": "user", "content": user_message})

            # 3. Call API
            stream = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.2,
                stream=True,
            )

            # 4. Yield Chunks
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    # Send text as a JSON event
                    yield json.dumps({"type": "token", "content": chunk.choices[0].delta.content}) + "\n"

        except Exception as e:
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

    
    def transcribe_audio(self, file_path: str) -> str:
        """
        Uses Groq's Whisper model to convert Audio -> Text.
        """
        try:
            with open(file_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(file_path, file.read()),
                    model="whisper-large-v3",
                    response_format="json",
                    temperature=0.0,
                    language = "en"
                )
            return transcription.text
        except Exception as e:
            return f"Error transcribing audio: {str(e)}"


# Create Singleton
chat_engine = ChatEngine()



