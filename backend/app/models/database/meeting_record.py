from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy import Column, Integer, String, JSON, BigInteger
from app.database.base import Base

class MeetingRecord(Base):
    __tablename__ = "meeting_records"

    id         = Column(Integer, primary_key=True, index=True, autoincrement=True)
    names      = Column(JSON,   nullable=False)   # ["Alice","Bob"]
    emails     = Column(JSON,   nullable=False)   # ["a@…","b@…"]
    summary    = Column(String(500), nullable=False)
    start_ts   = Column(BigInteger, nullable=False)  # UNIX timestamp (ms or s)
    end_ts     = Column(BigInteger, nullable=False)
    timezone   = Column(String(100), nullable=False)
    event_id   = Column(String(255), nullable=False, unique=True)