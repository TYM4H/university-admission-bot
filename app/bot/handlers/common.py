from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message()
async def echo_message(message: Message) -> None:
    await message.answer(
        f"Получил сообщение:\n{message.text}\n\n"
        "На следующем этапе вместо эхо подключим Ollama."
    )