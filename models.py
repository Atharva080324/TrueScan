from pydantic import BaseModel
from typing import List

class NewsRequest(BaseModel):
    topics: List[str]
    source_type: str