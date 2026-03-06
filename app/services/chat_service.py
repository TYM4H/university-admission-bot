class ChatService:
    async def get_response(self, user_id: int, text: str) -> str:
        text = (text or "").strip()

        if not text:
            return "Пустое сообщение я, увы, не телепатически распакую."

        return (
            f"Ты написал: {text}\n\n"
            "Сейчас это временный ответ через chat service.\n"
            "Следующим этапом сюда подключим Ollama."
        )


chat_service = ChatService()