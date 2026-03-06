from app.services.message_repository import message_repository


class ChatService:
    async def get_response(self, user_id: int, text: str) -> str:
        text = (text or "").strip()

        if not text:
            return "Пустое сообщение не очень удобно анализировать."

        await message_repository.save_message(
            user_id=user_id,
            role="user",
            text=text,
        )

        history = await message_repository.get_last_messages(
            user_id=user_id,
            limit=10,
        )

        history_lines = [
            f"{message.role}: {message.text}"
            for message in history
        ]

        history_text = "\n".join(history_lines)

        response = (
            "Сообщение сохранено в PostgreSQL.\n\n"
            f"Текущее сообщение: {text}\n\n"
            f"Сообщений в истории: {len(history)}\n\n"
            "Последние сообщения:\n"
            f"{history_text}"
        )

        await message_repository.save_message(
            user_id=user_id,
            role="bot",
            text=response,
        )

        return response


chat_service = ChatService()