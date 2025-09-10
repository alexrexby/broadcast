from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.dialects.postgresql import insert
import json
from datetime import datetime, date

from db.models import Theme


class ThemeService:
    """Сервис для работы с темами рассылок"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_theme(self, title: str, text: str, 
                          media: Optional[Dict[str, Any]] = None,
                          buttons: Optional[List[Dict[str, Any]]] = None,
                          schedule_date: Optional[datetime] = None) -> Theme:
        """Создать новую тему"""
        theme = Theme(
            title=title,
            text=text,
            media=media,
            buttons=buttons,
            schedule_date=schedule_date
        )
        self.db.add(theme)
        await self.db.commit()
        await self.db.refresh(theme)
        return theme
    
    async def get_theme_by_id(self, theme_id: int) -> Optional[Theme]:
        """Получить тему по ID"""
        result = await self.db.execute(
            select(Theme).where(Theme.id == theme_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_themes(self, offset: int = 0, limit: int = 100,
                            include_sent: bool = True) -> List[Theme]:
        """Получить список всех тем с пагинацией"""
        query = select(Theme)
        
        if not include_sent:
            query = query.where(Theme.is_sent == False)
        
        query = query.offset(offset).limit(limit).order_by(Theme.created_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_themes_count(self, include_sent: bool = True) -> int:
        """Получить количество тем"""
        query = select(func.count(Theme.id))
        
        if not include_sent:
            query = query.where(Theme.is_sent == False)
        
        result = await self.db.execute(query)
        return result.scalar()
    
    async def update_theme(self, theme_id: int, **kwargs) -> Optional[Theme]:
        """Обновить тему"""
        # Обновляем updated_at
        kwargs['updated_at'] = datetime.now()
        
        result = await self.db.execute(
            update(Theme)
            .where(Theme.id == theme_id)
            .values(**kwargs)
        )
        
        if result.rowcount == 0:
            return None
        
        await self.db.commit()
        return await self.get_theme_by_id(theme_id)
    
    async def delete_theme(self, theme_id: int) -> bool:
        """Удалить тему"""
        result = await self.db.execute(
            delete(Theme).where(Theme.id == theme_id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def mark_as_sent(self, theme_id: int) -> bool:
        """Отметить тему как отправленную"""
        result = await self.db.execute(
            update(Theme)
            .where(Theme.id == theme_id)
            .values(is_sent=True, updated_at=datetime.now())
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def get_next_queue_theme(self, exclude_ids: List[int] = None) -> Optional[Theme]:
        """Получить следующую тему из очереди (без запланированной даты)"""
        query = select(Theme).where(
            Theme.schedule_date.is_(None),
            Theme.is_sent == False
        )
        
        if exclude_ids:
            query = query.where(~Theme.id.in_(exclude_ids))
        
        query = query.order_by(Theme.created_at.asc()).limit(1)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_scheduled_themes_for_date(self, target_date: date) -> List[Theme]:
        """Получить темы, запланированные на конкретную дату"""
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        result = await self.db.execute(
            select(Theme).where(
                Theme.schedule_date >= start_of_day,
                Theme.schedule_date <= end_of_day,
                Theme.is_sent == False
            ).order_by(Theme.schedule_date.asc())
        )
        return result.scalars().all()
    
    async def get_overdue_themes(self, current_datetime: datetime) -> List[Theme]:
        """Получить просроченные темы (запланированные на прошедшее время)"""
        result = await self.db.execute(
            select(Theme).where(
                Theme.schedule_date < current_datetime,
                Theme.is_sent == False
            ).order_by(Theme.schedule_date.asc())
        )
        return result.scalars().all()
    
    async def schedule_theme(self, theme_id: int, schedule_date: datetime) -> bool:
        """Запланировать тему на конкретную дату"""
        result = await self.db.execute(
            update(Theme)
            .where(Theme.id == theme_id)
            .values(schedule_date=schedule_date, updated_at=datetime.now())
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def unschedule_theme(self, theme_id: int) -> bool:
        """Убрать тему из расписания (вернуть в очередь)"""
        result = await self.db.execute(
            update(Theme)
            .where(Theme.id == theme_id)
            .values(schedule_date=None, updated_at=datetime.now())
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def get_themes_by_status(self, is_sent: bool = False, 
                                  is_scheduled: Optional[bool] = None) -> List[Theme]:
        """Получить темы по статусу"""
        query = select(Theme).where(Theme.is_sent == is_sent)
        
        if is_scheduled is not None:
            if is_scheduled:
                query = query.where(Theme.schedule_date.is_not(None))
            else:
                query = query.where(Theme.schedule_date.is_(None))
        
        query = query.order_by(Theme.created_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def search_themes(self, search_query: str, 
                           offset: int = 0, limit: int = 50) -> List[Theme]:
        """Поиск тем по заголовку или тексту"""
        search_pattern = f"%{search_query}%"
        
        result = await self.db.execute(
            select(Theme).where(
                (Theme.title.ilike(search_pattern)) |
                (Theme.text.ilike(search_pattern))
            ).offset(offset).limit(limit).order_by(Theme.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_themes_statistics(self) -> Dict[str, int]:
        """Получить статистику по темам"""
        # Общее количество тем
        total_result = await self.db.execute(select(func.count(Theme.id)))
        total = total_result.scalar()
        
        # Отправленные темы
        sent_result = await self.db.execute(
            select(func.count(Theme.id)).where(Theme.is_sent == True)
        )
        sent = sent_result.scalar()
        
        # Запланированные темы
        scheduled_result = await self.db.execute(
            select(func.count(Theme.id)).where(
                Theme.schedule_date.is_not(None),
                Theme.is_sent == False
            )
        )
        scheduled = scheduled_result.scalar()
        
        # Темы в очереди
        queue_result = await self.db.execute(
            select(func.count(Theme.id)).where(
                Theme.schedule_date.is_(None),
                Theme.is_sent == False
            )
        )
        queue = queue_result.scalar()
        
        return {
            "total": total,
            "sent": sent,
            "scheduled": scheduled,
            "queue": queue,
            "pending": total - sent
        }
    
    async def duplicate_theme(self, theme_id: int, new_title: str = None) -> Optional[Theme]:
        """Дублировать тему"""
        original = await self.get_theme_by_id(theme_id)
        if not original:
            return None
        
        title = new_title or f"{original.title} (копия)"
        
        duplicate = Theme(
            title=title,
            text=original.text,
            media=original.media,
            buttons=original.buttons,
            schedule_date=None,  # Копия всегда идет в очередь
            is_sent=False
        )
        
        self.db.add(duplicate)
        await self.db.commit()
        await self.db.refresh(duplicate)
        return duplicate
