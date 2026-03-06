from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет. Я бот приемной комиссии университета.\n\n"
        "Сейчас у меня базовая версия, но дальше появятся ответы по документам, "
        "срокам поступления и информации об университете.\n\n"
        "Команды:\n"
        "/start - запуск\n"
        "/help - помощь"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Напиши вопрос в свободной форме.\n"
        "Например:\n"
        "Какие документы нужны для поступления?\n"
        "Когда начинается прием документов?\n"
        "Есть ли общежитие?"
    )