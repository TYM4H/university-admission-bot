from app.llm.ollama_client import ollama_client
from app.rag.retriever import retriever
from app.services.message_repository import message_repository


class ChatService:
    async def get_response(self, user_id: int, text: str) -> str:
        text = (text or "").strip()

        if not text:
            return "Пустое сообщение я не очень умею анализировать."

        await message_repository.save_message(
            user_id=user_id,
            role="user",
            text=text,
        )

        history = await message_repository.get_last_messages(
            user_id=user_id,
            limit=6,
        )

        relevant_documents = retriever.search(
            query=text,
            limit=4,
        )

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
            "Ты ассистент приемной комиссии университета. "
            "Отвечай кратко, ясно и по делу. "
            "Используй только информацию из предоставленного контекста документов. "
            "Если в контексте нет точного ответа на вопрос, прямо скажи, что в загруженных документах "
            "точного ответа не найдено. "
            "Не выдумывай документы, сроки, правила, льготы, стоимость и контакты."
        )

        dialog_lines = []
        for message in history[:-1]:
            role = "Пользователь" if message.role == "user" else "Ассистент"
            dialog_lines.append(f"{role}: {message.text}")

        dialog_text = "\n".join(dialog_lines)

        context_blocks = []
        for index, document in enumerate(relevant_documents, start=1):
            context_blocks.append(
                f"[Фрагмент {index}]\n{document['text']}"
            )

        context_text = "\n\n".join(context_blocks) if context_blocks else "Контекст не найден."

        return (
            f"{system_prompt}\n\n"
            f"Контекст из документов:\n{context_text}\n\n"
            f"История диалога:\n{dialog_text}\n\n"
            f"Текущий вопрос пользователя:\n{user_question}\n\n"
            f"Ответ ассистента:"
        )


chat_service = ChatService()