# Python standard library
import abc
import json

from .base import LLMClientBase

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
            MessagePassingInterface("system", "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)").to_dict(),
            MessagePassingInterface("user", prompt).to_dict(),
        ]
        return self._generate(messages)

    def generate_summary(self, prompt: str) -> dict:
        messages = [
            MessagePassingInterface("system", "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})").to_dict(),
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
            MessagePassingInterface("system", f"你是一個關聯度評估機器人，請評估新聞標題是否與「{prompt}」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)").to_dict(),
            MessagePassingInterface("user", news_title).to_dict(),
        ]
        return self._generate(messages)
