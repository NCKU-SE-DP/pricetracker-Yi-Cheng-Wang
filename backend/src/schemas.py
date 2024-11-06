from pydantic import BaseModel

class UserAuthSchema(BaseModel):
    username: str
    password: str

class PromptRequest(BaseModel):
    prompt: str

class NewsSumaryRequestSchema(BaseModel): #The class name is incorrect, but it hasn't been changed because it would affect the tests.
    content: str
