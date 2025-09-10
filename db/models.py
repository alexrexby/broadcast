from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List, Dict, Any

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_subscribed = Column(Boolean, default=False)  # подписан на все обязательные каналы
    subscriptions = Column(JSON, default=list)  # список ID каналов на которые подписан
    registration_date = Column(DateTime, default=func.now())
    last_delivery_date = Column(DateTime, nullable=True)
    daily_theme_history = Column(JSON, default=list)  # история отправленных тем
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class Theme(Base):
    __tablename__ = "themes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    media = Column(JSON, nullable=True)  # {"type": "photo/video", "file_id": "...", "caption": "..."}
    buttons = Column(JSON, nullable=True)  # inline keyboard buttons
    schedule_date = Column(DateTime, nullable=True)  # null если в очереди
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Theme(id={self.id}, title={self.title})>"


class BroadcastTask(Base):
    __tablename__ = "broadcast_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)  # daily/manual
    title = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    media = Column(JSON, nullable=True)
    buttons = Column(JSON, nullable=True)
    audience = Column(JSON, nullable=False)  # список user_id или критерии фильтрации
    scheduled_for = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="pending")  # pending/running/completed/failed
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    delivery_report = Column(JSON, default=dict)  # детальный отчет о доставке
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<BroadcastTask(id={self.id}, type={self.type}, status={self.status})>"


class Config(Base):
    __tablename__ = "config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Config(key={self.key})>"


class DeliveryLog(Base):
    __tablename__ = "delivery_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    broadcast_task_id = Column(Integer, nullable=True)  # null для ежедневных рассылок
    user_id = Column(Integer, nullable=False)
    telegram_id = Column(Integer, nullable=False)
    message_type = Column(String(50), nullable=False)  # daily_theme/broadcast/subscription_check
    status = Column(String(50), nullable=False)  # sent/delivered/failed/blocked
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<DeliveryLog(telegram_id={self.telegram_id}, status={self.status})>"


# Дефолтные настройки конфигурации
DEFAULT_CONFIG = {
    "bot_token": {
        "value": "",
        "description": "Токен Telegram бота"
    },
    "required_channels": {
        "value": "[]",
        "description": "Список обязательных каналов для подписки (JSON массив ID каналов)"
    },
    "daily_broadcast_time": {
        "value": "09:00",
        "description": "Время ежедневной рассылки (HH:MM)"
    },
    "timezone": {
        "value": "Europe/Moscow",
        "description": "Часовой пояс для рассылок"
    },
    "rate_limit": {
        "value": "30",
        "description": "Лимит отправки сообщений в секунду"
    },
    "welcome_message": {
        "value": "Добро пожаловать! Для получения ежедневных тем подпишитесь на наши каналы:",
        "description": "Приветственное сообщение для новых пользователей"
    },
    "subscription_required_message": {
        "value": "Для получения контента необходимо подписаться на все обязательные каналы:",
        "description": "Сообщение о необходимости подписки"
    }
}
