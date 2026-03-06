from sqlalchemy import select

from app.db.models.message import Message
from app.db.session import SessionLocal


class MessageRepository:
    async def save_message(self, user_id: int, role: str, text: str):
        async with SessionLocal() as session:
            message = Message(
                user_id=user_id,
                role=role,
                text=text,
            )
            session.add(message)
            await session.commit()

    async def get_last_messages(self, user_id: int, limit: int = 10):
        async with SessionLocal() as session:
            stmt = (
                select(Message)
                .where(Message.user_id == user_id)
                .order_by(Message.created_at.desc(), Message.id.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            messages = result.scalars().all()

        return list(reversed(messages))


message_repository = MessageRepository()