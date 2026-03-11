import importlib
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock, call, patch

from app.core.config import settings


def make_module(name: str, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    return module


def import_with_stubs(target: str, stubs: dict[str, types.ModuleType]):
    sys.modules.pop(target, None)
    with patch.dict(sys.modules, stubs):
        module = importlib.import_module(target)
    return module


class ChatServiceRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_response_runs_retrieval_in_worker_thread(self):
        fake_retriever = types.SimpleNamespace(search=Mock(return_value=[]))
        fake_ollama_client = types.SimpleNamespace(generate=AsyncMock(return_value="ok"))
        fake_repository = types.SimpleNamespace(
            save_message=AsyncMock(),
            get_last_messages=AsyncMock(return_value=[]),
        )

        chat_service_module = import_with_stubs(
            "app.services.chat_service",
            {
                "app.rag.retriever": make_module(
                    "app.rag.retriever",
                    retriever=fake_retriever,
                ),
                "app.llm.ollama_client": make_module(
                    "app.llm.ollama_client",
                    ollama_client=fake_ollama_client,
                ),
                "app.services.message_repository": make_module(
                    "app.services.message_repository",
                    message_repository=fake_repository,
                ),
            },
        )
        self.addCleanup(sys.modules.pop, "app.services.chat_service", None)

        service = chat_service_module.ChatService()
        to_thread = AsyncMock(return_value=[])

        with patch.object(chat_service_module.asyncio, "to_thread", to_thread):
            response = await service.get_response(user_id=1, text="Когда подача документов?")

        self.assertEqual(response, "ok")
        to_thread.assert_awaited_once_with(
            fake_retriever.search,
            "Когда подача документов?",
        )

    def test_build_prompt_keeps_instruction_boundaries(self):
        chat_service_module = import_with_stubs(
            "app.services.chat_service",
            {
                "app.rag.retriever": make_module(
                    "app.rag.retriever",
                    retriever=types.SimpleNamespace(search=Mock(return_value=[])),
                ),
                "app.llm.ollama_client": make_module(
                    "app.llm.ollama_client",
                    ollama_client=types.SimpleNamespace(generate=AsyncMock(return_value="ok")),
                ),
                "app.services.message_repository": make_module(
                    "app.services.message_repository",
                    message_repository=types.SimpleNamespace(
                        save_message=AsyncMock(),
                        get_last_messages=AsyncMock(return_value=[]),
                    ),
                ),
            },
        )
        self.addCleanup(sys.modules.pop, "app.services.chat_service", None)

        prompt = chat_service_module.ChatService()._build_prompt(
            history=[],
            relevant_documents=[],
            user_question="Тестовый вопрос",
        )

        self.assertIn("есть в истории. Отвечай только", prompt)
        self.assertIn("комиссии и поступления. Если ответ", prompt)


class VectorStoreRegressionTests(unittest.TestCase):
    def test_recreate_collection_replaces_existing_collection(self):
        fake_qdrant_client = Mock()
        fake_qdrant_client.get_collections.side_effect = [
            types.SimpleNamespace(
                collections=[types.SimpleNamespace(name=settings.qdrant_collection)]
            ),
            types.SimpleNamespace(collections=[]),
        ]

        vector_store_module = import_with_stubs(
            "app.rag.vector_store",
            {
                "app.rag.qdrant_client": make_module(
                    "app.rag.qdrant_client",
                    qdrant_client=fake_qdrant_client,
                ),
                "app.services.embedding_service": make_module(
                    "app.services.embedding_service",
                    embedding_service=types.SimpleNamespace(vector_size=1024),
                ),
            },
        )
        self.addCleanup(sys.modules.pop, "app.rag.vector_store", None)

        vector_store_module.VectorStore().recreate_collection()

        self.assertEqual(
            fake_qdrant_client.method_calls[:3],
            [
                call.get_collections(),
                call.delete_collection(settings.qdrant_collection),
                call.get_collections(),
            ],
        )
        fake_qdrant_client.create_collection.assert_called_once()


if __name__ == "__main__":
    unittest.main()
