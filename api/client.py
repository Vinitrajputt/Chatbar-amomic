
from openai import OpenAI

class LocalAIClient:
    """
    A client for interacting with a local OpenAI-compatible server.
    """
    def __init__(self, base_url="http://127.0.0.1:1234/v1"):
        self.client = OpenAI(base_url=base_url, api_key="not-needed")
        self.model = "llama-3.2-1b-instruct"

    def get_streaming_response(self, prompt: str):
        """
        Sends a prompt to the server and yields the response chunks.
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                stream=True,
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            print(f"Error connecting to local AI server: {e}")
            yield "Error: Could not connect to the local server. Please ensure it's running."
