import abc

class MessagePassingInterface:
    """
    A class to represent a message in the chat interface.
    
    Attributes:
        role (str): The role of the message sender (e.g., 'system', 'user').
        content (str): The content of the message.
    """

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self):
        return {"role": self.role, "content": self.content}

class LLMClientBase(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def generate_keywords(self, prompt: str) -> str:
        """
        Extract keywords from the given prompt.
        """
        return NotImplemented

    @abc.abstractmethod
    def generate_summary(self, prompt: str) -> dict:
        """
        Generate a summary based on the given prompt.
        """
        return NotImplemented

    @abc.abstractmethod
    def evaluate_relevance(self, news_title: str, prompt: str) -> str:
        """
        Evaluate the relevance of the news title to the given prompt.
        """
        return NotImplemented

    @staticmethod
    def log_error(error_message: str) -> None:
        """
        Log the error message for debugging purposes.
        """
        print(f"Error: {error_message}")
