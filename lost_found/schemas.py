from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ItemCreate(BaseModel):
    title: str
    description: str
    location: Optional[str] = None
    contact: str
    category: Optional[str] = None


class ItemOut(BaseModel):
    id: int
    type: str
    title: str
    description: str
    location: Optional[str]
    contact: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MatchOut(BaseModel):
    item: ItemOut
    score: float
