from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет. Я бот приемной комиссии.\n"
        "Пока я в базовой версии, но уже живой.\n\n"
        "Команды:\n"
        "/start - запуск\n"
        "/help - помощь"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Напиши вопрос про поступление, документы, сроки или университет.\n"
        "Пока это стартовый каркас, дальше прикрутим LLM и RAG."
    )