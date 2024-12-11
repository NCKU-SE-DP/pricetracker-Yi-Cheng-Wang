import aisuite as ai
from .client_base import LLMClientTemplate

class AnthropicClient(LLMClientTemplate):
    def __init__(self, _api_key: str, model: str):
        super().__init__(_api_key, model)

    def _initialize_client(self):
        self.client = ai.Client({"anthropic": {"api_key": self.api_key}})
