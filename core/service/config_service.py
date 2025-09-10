import json
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert

from db.models import Config, DEFAULT_CONFIG


class ConfigService:
    """Сервис для работы с настройками"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_config(self, key: str) -> Optional[str]:
        """Получить значение конфигурации по ключу"""
        result = await self.db.execute(
            select(Config.value).where(Config.key == key)
        )
        config = result.scalar_one_or_none()
        return config
    
    async def set_config(self, key: str, value: str, description: str = None) -> None:
        """Установить значение конфигурации"""
        stmt = insert(Config).values(
            key=key,
            value=value,
            description=description
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['key'],
            set_=dict(value=stmt.excluded.value, description=stmt.excluded.description)
        )
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def get_all_config(self) -> Dict[str, Dict[str, str]]:
        """Получить все настройки"""
        result = await self.db.execute(
            select(Config.key, Config.value, Config.description)
        )
        configs = result.fetchall()
        
        return {
            config.key: {
                "value": config.value or "",
                "description": config.description or ""
            }
            for config in configs
        }
    
    async def delete_config(self, key: str) -> bool:
        """Удалить настройку"""
        result = await self.db.execute(
            delete(Config).where(Config.key == key)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    # Специфичные методы для важных настроек
    
    async def get_bot_token(self) -> Optional[str]:
        """Получить токен бота"""
        return await self.get_config("bot_token")
    
    async def set_bot_token(self, token: str) -> None:
        """Установить токен бота"""
        await self.set_config("bot_token", token, "Токен Telegram бота")
    
    async def get_required_channels(self) -> List[int]:
        """Получить список обязательных каналов"""
        channels_json = await self.get_config("required_channels")
        if not channels_json:
            return []
        try:
            channels = json.loads(channels_json)
            return [int(ch) for ch in channels if str(ch).lstrip('-').isdigit()]
        except (json.JSONDecodeError, ValueError):
            return []
    
    async def set_required_channels(self, channels: List[int]) -> None:
        """Установить список обязательных каналов"""
        channels_json = json.dumps(channels)
        await self.set_config(
            "required_channels", 
            channels_json, 
            "Список обязательных каналов для подписки"
        )
    
    async def get_daily_broadcast_time(self) -> str:
        """Получить время ежедневной рассылки"""
        time_str = await self.get_config("daily_broadcast_time")
        return time_str or "09:00"
    
    async def set_daily_broadcast_time(self, time_str: str) -> None:
        """Установить время ежедневной рассылки"""
        await self.set_config(
            "daily_broadcast_time", 
            time_str, 
            "Время ежедневной рассылки (HH:MM)"
        )
    
    async def get_timezone(self) -> str:
        """Получить часовой пояс"""
        timezone = await self.get_config("timezone")
        return timezone or "Europe/Moscow"
    
    async def set_timezone(self, timezone: str) -> None:
        """Установить часовой пояс"""
        await self.set_config("timezone", timezone, "Часовой пояс для рассылок")
    
    async def get_rate_limit(self) -> int:
        """Получить лимит отправки сообщений"""
        rate_str = await self.get_config("rate_limit")
        try:
            return int(rate_str) if rate_str else 30
        except ValueError:
            return 30
    
    async def set_rate_limit(self, rate: int) -> None:
        """Установить лимит отправки сообщений"""
        await self.set_config(
            "rate_limit", 
            str(rate), 
            "Лимит отправки сообщений в секунду"
        )
    
    async def get_welcome_message(self) -> str:
        """Получить приветственное сообщение"""
        message = await self.get_config("welcome_message")
        return message or DEFAULT_CONFIG["welcome_message"]["value"]
    
    async def set_welcome_message(self, message: str) -> None:
        """Установить приветственное сообщение"""
        await self.set_config(
            "welcome_message", 
            message, 
            "Приветственное сообщение для новых пользователей"
        )
    
    async def get_subscription_required_message(self) -> str:
        """Получить сообщение о необходимости подписки"""
        message = await self.get_config("subscription_required_message")
        return message or DEFAULT_CONFIG["subscription_required_message"]["value"]
    
    async def set_subscription_required_message(self, message: str) -> None:
        """Установить сообщение о необходимости подписки"""
        await self.set_config(
            "subscription_required_message", 
            message, 
            "Сообщение о необходимости подписки на каналы"
        )
    
    async def init_default_config(self) -> None:
        """Инициализировать дефолтные настройки"""
        for key, config in DEFAULT_CONFIG.items():
            existing = await self.get_config(key)
            if existing is None:
                await self.set_config(key, config["value"], config["description"])
