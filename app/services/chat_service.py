from app.llm.ollama_client import ollama_client
from app.services.message_repository import message_repository


class ChatService:
    async def get_response(self, user_id: int, text: str) -> str:
        text = (text or "").strip()

        if not text:
            return "Пустое сообщение я не очень умею читать между строк."

        await message_repository.save_message(
            user_id=user_id,
            role="user",
            text=text,
        )

        history = await message_repository.get_last_messages(
            user_id=user_id,
            limit=10,
        )

        prompt = self._build_prompt(history)

        response = await ollama_client.generate(prompt)

        await message_repository.save_message(
            user_id=user_id,
            role="bot",
            text=response,
        )

        return response

    def _build_prompt(self, history) -> str:
        system_prompt = (
            "Ты ассистент приемной комиссии университета. "
            "Отвечай кратко и по делу. "
            "Игнорируй грубый или неформальный язык пользователя и продолжай диалог спокойно. "
            "Не выдумывай факты о правилах поступления."
        )

        dialog_lines = []
        for message in history:
            role = "Пользователь" if message.role == "user" else "Ассистент"
            dialog_lines.append(f"{role}: {message.text}")

        dialog_text = "\n".join(dialog_lines)

        return (
            f"{system_prompt}\n\n"
            f"Диалог:\n{dialog_text}\n\n"
            f"Ответ ассистента:"
        )


chat_service = ChatService()