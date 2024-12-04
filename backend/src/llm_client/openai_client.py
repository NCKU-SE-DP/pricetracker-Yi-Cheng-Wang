# Python standard library
import json
from openai import OpenAI, APIError, RateLimitError

class MessagePassingInterface:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self):
        return {"role": self.role, "content": self.content}

class LLMClient:
    def __init__(self, _api_key: str):
        try:
            self.openai_client = OpenAI(api_key=_api_key)
        except APIError as error:
            raise Exception(f"[LLMClient] An error occurred: {error}")

    def _generate(self, messages: list) -> str:
        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )
            return completion.choices[0].message.content
        except APIError as error:
            print(f"[OpenAI] An error occurred: {error}")
            return ""
        except RateLimitError as error:
            print(f"[OpenAI] Rate limit exceeded: {error}")
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
        response = self._generate(messages)
        return json.loads(response)

    def evaluate_relevance(self, news_title: str, prompt: str = "民生用品的價格變化") -> str:
        messages = [
            MessagePassingInterface("system", f"你是一個關聯度評估機器人，請評估新聞標題是否與「{prompt}」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)").to_dict(),
            MessagePassingInterface("user", news_title).to_dict(),
        ]
        return self._generate(messages)
