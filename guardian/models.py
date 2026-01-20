from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    text: str

class AnalyzeResponse(BaseModel):
    toxicity: float
    sexual: float
    violence: float
    illegal: float