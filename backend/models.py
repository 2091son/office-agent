from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), default="employee")  # admin / employee
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    logs = relationship("OperationLog", back_populates="user")


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)       # 比如 "生成周报"
    detail = Column(Text, default="")                   # 具体做了什么事
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="logs")