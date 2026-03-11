from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Здравствуйте! Я бот приёмной комиссии МТУСИ.\n\n"
        "Я помогаю с вопросами о поступлении, документах, сроках подачи, "
        "вступительных испытаниях и другой информации для абитуриентов.\n\n"
        "Вы можете сразу задать вопрос в свободной форме.\n\n"
        "Например:\n"
        "- Какие документы нужны для поступления?\n"
        "- С какого числа можно подавать документы?\n"
        "- Где находится приёмная комиссия?\n\n"
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
