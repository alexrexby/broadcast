import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения"""
    
    # База данных
    database_url: str = Field(..., env="DATABASE_URL")
    
    # API настройки
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Админка
    admin_password: str = Field(..., env="ADMIN_PASSWORD")
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # Логирование
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Настройки рассылки (дефолтные, переопределяются в админке)
    daily_broadcast_time: str = Field(default="09:00", env="DAILY_BROADCAST_TIME")
    timezone: str = Field(default="Europe/Moscow", env="TIMEZONE")
    rate_limit: int = Field(default=30, env="RATE_LIMIT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Глобальный экземпляр настроек
settings = Settings()
