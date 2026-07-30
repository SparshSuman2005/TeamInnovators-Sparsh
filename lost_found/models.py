from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from .database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True)          # "lost" or "found"
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String, nullable=True)
    contact = Column(String, nullable=False)
    status = Column(String, default="open")    # open / matched / resolved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
