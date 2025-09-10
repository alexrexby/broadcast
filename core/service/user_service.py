from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.dialects.postgresql import insert
import json
from datetime import datetime

from db.models import User, DeliveryLog


class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_user(self, telegram_id: int, username: str = None, 
                                first_name: str = None, last_name: str = None) -> User:
        """Получить пользователя или создать нового"""
        # Попытка найти существующего пользователя
        result = await self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Обновить данные если изменились
            if (user.username != username or 
                user.first_name != first_name or 
                user.last_name != last_name):
                
                await self.db.execute(
                    update(User)
                    .where(User.telegram_id == telegram_id)
                    .values(
                        username=username,
                        first_name=first_name,
                        last_name=last_name
                    )
                )
                await self.db.commit()
            return user
        
        # Создать нового пользователя
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            subscriptions=[],
            daily_theme_history=[]
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_user_subscriptions(self, telegram_id: int, 
                                       subscriptions: List[int]) -> bool:
        """Обновить список подписок пользователя"""
        result = await self.db.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(subscriptions=subscriptions)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def update_subscription_status(self, telegram_id: int, 
                                        is_subscribed: bool) -> bool:
        """Обновить статус подписки пользователя"""
        result = await self.db.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_subscribed=is_subscribed)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        result = await self.db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_users(self, offset: int = 0, limit: int = 100, 
                           is_subscribed: Optional[bool] = None) -> List[User]:
        """Получить список всех пользователей с фильтрацией"""
        query = select(User)
        
        if is_subscribed is not None:
            query = query.where(User.is_subscribed == is_subscribed)
        
        query = query.offset(offset).limit(limit).order_by(User.registration_date.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_users_count(self, is_subscribed: Optional[bool] = None) -> int:
        """Получить количество пользователей"""
        query = select(func.count(User.id))
        
        if is_subscribed is not None:
            query = query.where(User.is_subscribed == is_subscribed)
        
        result = await self.db.execute(query)
        return result.scalar()
    
    async def get_subscribed_users(self) -> List[User]:
        """Получить всех подписанных пользователей для рассылки"""
        result = await self.db.execute(
            select(User).where(
                User.is_subscribed == True,
                User.is_active == True
            )
        )
        return result.scalars().all()
    
    async def add_theme_to_history(self, telegram_id: int, theme_id: int) -> bool:
        """Добавить тему в историю пользователя"""
        user = await self.get_user_by_telegram_id(telegram_id)
        if not user:
            return False
        
        history = user.daily_theme_history or []
        if theme_id not in history:
            history.append(theme_id)
            # Ограничиваем историю последними 100 темами
            if len(history) > 100:
                history = history[-100:]
        
        await self.db.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(
                daily_theme_history=history,
                last_delivery_date=datetime.now()
            )
        )
        await self.db.commit()
        return True
    
    async def deactivate_user(self, telegram_id: int) -> bool:
        """Деактивировать пользователя (заблокировал бота)"""
        result = await self.db.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(is_active=False)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def log_delivery(self, telegram_id: int, message_type: str, 
                          status: str, error_message: str = None,
                          broadcast_task_id: int = None) -> None:
        """Записать лог доставки сообщения"""
        user = await self.get_user_by_telegram_id(telegram_id)
        user_id = user.id if user else None
        
        log = DeliveryLog(
            broadcast_task_id=broadcast_task_id,
            user_id=user_id,
            telegram_id=telegram_id,
            message_type=message_type,
            status=status,
            error_message=error_message
        )
        self.db.add(log)
        await self.db.commit()
