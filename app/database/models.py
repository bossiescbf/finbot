from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, BigInteger, Text, Numeric, DateTime, 
    ForeignKey, CheckConstraint, func, Boolean, String
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=True)
    username = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    timezone = Column(String(50), default='Europe/Moscow', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Настройки пользователя
    currency = Column(String(3), default='RUB', nullable=False)
    notification_enabled = Column(Boolean, default=True, nullable=False)
    daily_limit = Column(Numeric(12, 2), nullable=True)
    monthly_limit = Column(Numeric(12, 2), nullable=True)
    
    # Связи
    operations = relationship('Operation', back_populates='user', cascade='all, delete-orphan')
    categories = relationship('Category', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(10), nullable=True)  # Эмодзи иконка
    color = Column(String(7), nullable=True)  # HEX цвет
    is_income = Column(Boolean, default=False, nullable=False)  # True для доходов, False для расходов
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Связи
    user = relationship('User', back_populates='categories')
    operations = relationship('Operation', back_populates='category')
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', is_income={self.is_income})>"

class Operation(Base):
    __tablename__ = 'operations'
    __table_args__ = (
        CheckConstraint("type IN ('income','expense')", name='chk_type'),
        CheckConstraint("amount > 0", name='chk_positive_amount'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Основные поля
    type = Column(Text, nullable=False)  # 'income' или 'expense'
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=True)
    
    # Временные метки
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Дополнительные поля
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurring_period = Column(String(20), nullable=True)  # 'daily', 'weekly', 'monthly'
    tags = Column(Text, nullable=True)  # JSON строка с тегами
    location = Column(Text, nullable=True)  # Геолокация
    receipt_url = Column(Text, nullable=True)  # Ссылка на чек
    
    # Связи
    user = relationship('User', back_populates='operations')
    category = relationship('Category', back_populates='operations')
    
    @property
    def category_name(self):
        """Получить имя категории или значение по умолчанию"""
        return self.category.name if self.category else 'Без категории'
    
    def __repr__(self):
        return f"<Operation(id={self.id}, type='{self.type}', amount={self.amount}, category='{self.category_name}')>"

class UserSession(Base):
    """Таблица для хранения пользовательских сессий и состояний FSM"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    session_data = Column(Text, nullable=True)  # JSON данные FSM состояния
    state = Column(String(100), nullable=True)  # Текущее FSM состояние
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Связи
    user = relationship('User')

class Budget(Base):
    """Таблица для бюджетов по категориям"""
    __tablename__ = 'budgets'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # Бюджет
    limit_amount = Column(Numeric(12, 2), nullable=False)
    period = Column(String(20), nullable=False, default='monthly')  # 'daily', 'weekly', 'monthly'
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Статус
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Связи
    user = relationship('User')
    category = relationship('Category')
    
    def __repr__(self):
        return f"<Budget(id={self.id}, limit={self.limit_amount}, period='{self.period}')>"