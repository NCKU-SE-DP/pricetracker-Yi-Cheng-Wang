# Python standard library
import abc
import json

from .base import LLMClientBase
from .messages import KEYWORD_EXTRACTION_SYSTEM_MESSAGE, GENERATE_SUMMARY_SYSTEM_MESSAGE, EVALUATE_RELEVANCE_SYSTEM_MESSAGE

class MessagePassingInterface:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self):
        return {"role": self.role, "content": self.content}

class LLMClientTemplate(LLMClientBase, abc.ABC):
    def __init__(self, _api_key: str, model: str):
        self.api_key = _api_key
        self.model= model
        self._initialize_client()

    @abc.abstractmethod
    def _initialize_client(self):
        ...

    def _generate(self, messages: list) -> str:
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            return completion.choices[0].message.content
        except Exception as error:
            print(f"[LLMClientTemplate] An error occurred: {error}")
            return ""

    def extract_search_keywords(self, prompt: str) -> str:
        messages = [
            MessagePassingInterface("system", KEYWORD_EXTRACTION_SYSTEM_MESSAGE).to_dict(),
            MessagePassingInterface("user", prompt).to_dict(),
        ]
        return self._generate(messages)

    def generate_summary(self, prompt: str) -> dict:
        messages = [
            MessagePassingInterface("system", GENERATE_SUMMARY_SYSTEM_MESSAGE).to_dict(),
            MessagePassingInterface("user", prompt).to_dict(),
        ]
        
        for attempt in range(3): 
            response = self._generate(messages)
            response = response.replace("'", '"')
            try:
                return json.loads(response)  
            except json.JSONDecodeError:
                raise ValueError("[generate_summary] 無法解析為 JSON，請檢查回應格式。")

    def evaluate_relevance(self, news_title: str, prompt: str = "民生用品的價格變化") -> str:
        messages = [
            MessagePassingInterface("system", EVALUATE_RELEVANCE_SYSTEM_MESSAGE.format(prompt=prompt)).to_dict(),
            MessagePassingInterface("user", news_title).to_dict(),
        ]
        return self._generate(messages)
