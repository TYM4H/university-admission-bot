from aiogram import Router
from aiogram.types import Message

from app.services.chat_service import chat_service

router = Router()


@router.message()
async def handle_message(message: Message) -> None:
    response = await chat_service.get_response(
        user_id=message.from_user.id,
        text=message.text or "",
    )
    await message.answer(response)