from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, Text, Numeric,
    DateTime, ForeignKey, CheckConstraint, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Объявляем базовый класс для моделей
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=True)
    username = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    operations = relationship('Operation', back_populates='user', cascade='all, delete-orphan')

class Operation(Base):
    __tablename__ = 'operations'
    __table_args__ = (
        CheckConstraint("type IN ('income','expense')", name='chk_type'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    type = Column(Text, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    category = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship('User', back_populates='operations')
