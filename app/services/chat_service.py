import asyncio
import logging
import time

from app.llm.ollama_client import ollama_client
from app.rag.retriever import retriever
from app.services.message_repository import message_repository


logger = logging.getLogger("rag")


class ChatService:
    async def get_response(self, user_id: int, text: str) -> str:
        request_start = time.perf_counter()

        text = (text or "").strip()

        if not text:
            return "Пустое сообщение я анализировать не умею."

        logger.info(f"USER {user_id}: {text}")

        await message_repository.save_message(
            user_id=user_id,
            role="user",
            text=text,
        )

        history = await message_repository.get_last_messages(
            user_id=user_id,
            limit=6,
        )

        retrieval_start = time.perf_counter()
        relevant_documents = await asyncio.to_thread(retriever.search, text)
        retrieval_time = time.perf_counter() - retrieval_start

        logger.info(f"Retrieval time: {retrieval_time:.3f}s")
        logger.info(f"Documents retrieved: {len(relevant_documents)}")

        if relevant_documents:
            logger.info("CONTEXT SENT TO LLM:")
            for index, document in enumerate(relevant_documents, start=1):
                preview = document["text"][:200].replace("\n", " ")
                logger.info(
                    f"CTX {index} | "
                    f"score={document['score']:.3f} | "
                    f"source={document['source']} | "
                    f"text={preview}"
                )
        else:
            logger.warning("No context found for this query")

        prompt_start = time.perf_counter()
        prompt = self._build_prompt(
            history=history,
            relevant_documents=relevant_documents,
            user_question=text,
        )
        prompt_time = time.perf_counter() - prompt_start

        logger.info(f"Prompt build time: {prompt_time:.3f}s")
        logger.info(f"PROMPT LENGTH: {len(prompt)}")

        llm_start = time.perf_counter()
        response = await ollama_client.generate(prompt)
        llm_time = time.perf_counter() - llm_start

        logger.info(f"LLM generation time: {llm_time:.3f}s")
        logger.info(f"BOT {user_id}: {response[:300]}")

        await message_repository.save_message(
            user_id=user_id,
            role="bot",
            text=response,
        )

        total_time = time.perf_counter() - request_start
        logger.info(f"TOTAL REQUEST TIME: {total_time:.3f}s")

        return response

    def _build_prompt(
        self,
        history,
        relevant_documents: list[dict],
        user_question: str,
    ) -> str:
        system_prompt = (
            "Ты ассистент приёмной комиссии университета МТУСИ. "
            "Отвечай кратко, понятно и вежливо. "
            "Если пользователь просто здоровается, начинает разговор или пишет сообщение без конкретного вопроса, "
            "вежливо поприветствуй его и предложи задать вопрос о поступлении. "
            "Не надо приветствовать повторно, если это уже есть в истории. "
            "Отвечай только на основе предоставленного контекста. "
            "Не придумывай факты, которых нет в контексте. "
            "Не ссылайся на номера фрагментов, документов или страниц. "
            "Если вопрос не относится к теме поступления или обучения в университете, "
            "вежливо ответь, что ты помогаешь только по вопросам приёмной комиссии и поступления. "
            "Не отвечай на оффтоп даже частично и не пытайся угадывать ответ. "
            "Если точного ответа в контексте нет, скажи, что информация отсутствует в базе знаний и не говори ничего лишнего. "
            "Если в контексте есть важные условия, ограничения, исключения, сроки или оговорки, обязательно включи их в ответ. "
            "Если вопрос сформулирован слишком широко или двусмысленно, а в контексте есть разные ответы для разных случаев, "
            "сначала кратко перечисли эти случаи по контексту и только потом дай ответ по каждому случаю. "
            "Если вопрос про категорию поступающих, форму обучения, основу обучения или уровень образования, "
            "не опускай соответствующие уточнения из контекста. "
            "Если вопрос пользователя предполагает правило с ограничением, не отвечай общими словами, а назови само ограничение. "
            "Если ответ на вопрос содержится в контексте, используй только контекст и не говори ничего лишнего."
        )

        dialog_lines = []
        for message in history[:-1]:
            if message.role == "user":
                dialog_lines.append(f"Пользователь: {message.text}")
            elif message.role == "bot":
                dialog_lines.append(f"Ассистент: {message.text}")

        dialog_text = "\n".join(dialog_lines[-3:])

        logger.info(f"DIALOG HISTORY PASSED TO LLM:\n{dialog_text}")

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
