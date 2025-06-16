from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from database.database import Base
from datetime import datetime

class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False)
    stack = Column(Text, nullable=True)
    source = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_agent = Column(String(500), nullable=True)
    url = Column(String(500), nullable=False)
    error_type = Column(String(50), nullable=True)
    severity = Column(String(20), default="error", nullable=False)  # error, warning, info
    resolved = Column(Integer, default=0, nullable=False)  # 0 = unresolved, 1 = resolved
    additional_data = Column(JSON, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "stack": self.stack,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_agent": self.user_agent,
            "url": self.url,
            "error_type": self.error_type,
            "severity": self.severity,
            "resolved": self.resolved,
            "additional_data": self.additional_data
        }