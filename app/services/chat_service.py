from app.llm.ollama_client import ollama_client
from app.rag.retriever import retriever
from app.services.message_repository import message_repository


class ChatService:
    async def get_response(self, user_id: int, text: str) -> str:
        text = (text or "").strip()

        if not text:
            return "Пустое сообщение я анализировать не умею."

        await message_repository.save_message(
            user_id=user_id,
            role="user",
            text=text,
        )

        history = await message_repository.get_last_messages(
            user_id=user_id,
            limit=6,
        )

        relevant_documents = retriever.search(text)

        prompt = self._build_prompt(
            history=history,
            relevant_documents=relevant_documents,
            user_question=text,
        )

        response = await ollama_client.generate(prompt)

        await message_repository.save_message(
            user_id=user_id,
            role="bot",
            text=response,
        )

        return response

    def _build_prompt(
        self,
        history,
        relevant_documents: list[dict],
        user_question: str,
    ) -> str:
        system_prompt = (
            "Ты ассистент приёмной комиссии университета. "
            "Отвечай кратко, понятно и вежливо. "
            "Если пользователь просто здоровается, начинает разговор или пишет сообщение без конкретного вопроса, "
            "вежливо поприветствуй его и предложи задать вопрос о поступлении. "
            "Если вопрос относится к поступлению, документам, срокам, вступительным испытаниям, льготам, "
            "общежитию, платному обучению или обучению в университете, "
            "отвечай только на основе предоставленного контекста. "
            "Не ссылайся на номера фрагментов, документов или страниц. "
            "Если точного ответа в контексте нет, скажи, что информация отсутствует в базе знаний. "
            "Если вопрос не относится к теме поступления или обучения в университете, "
            "вежливо ответь, что ты помогаешь только по вопросам приёмной комиссии и поступления."
        )

        dialog_lines = []
        for message in history[:-1]:
            role = "Пользователь" if message.role == "user" else "Ассистент"
            dialog_lines.append(f"{role}: {message.text}")

        dialog_text = "\n".join(dialog_lines)

        context_blocks = []
        for index, document in enumerate(relevant_documents, start=1):
            context_blocks.append(f"[Контекст {index}]\n{document['text']}")

        context_text = "\n\n".join(context_blocks) if context_blocks else "Контекст не найден."

        return (
            f"{system_prompt}\n\n"
            f"Контекст из базы знаний:\n{context_text}\n\n"
            f"История диалога:\n{dialog_text}\n\n"
            f"Текущий вопрос пользователя:\n{user_question}\n\n"
            f"Ответ ассистента:"
        )


chat_service = ChatService()