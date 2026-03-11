import importlib
import sys
import types
import unittest
import uuid
from unittest.mock import patch

from qdrant_client import QdrantClient


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


class VectorStoreQdrantIntegrationTests(unittest.TestCase):
    def test_recreate_collection_removes_old_points_before_reindex(self):
        local_qdrant = QdrantClient(location=":memory:")
        collection_name = f"test_{uuid.uuid4().hex}"

        vector_store_module = import_with_stubs(
            "app.rag.vector_store",
            {
                "app.rag.qdrant_client": make_module(
                    "app.rag.qdrant_client",
                    qdrant_client=local_qdrant,
                ),
                "app.services.embedding_service": make_module(
                    "app.services.embedding_service",
                    embedding_service=types.SimpleNamespace(vector_size=2),
                ),
            },
        )
        self.addCleanup(sys.modules.pop, "app.rag.vector_store", None)

        store = vector_store_module.VectorStore()

        first_documents = [
            {
                "text": "old chunk",
                "metadata": {
                    "source": "old.txt",
                    "page": None,
                    "chunk_index": 0,
                },
            }
        ]
        second_documents = [
            {
                "text": "new chunk",
                "metadata": {
                    "source": "new.txt",
                    "page": None,
                    "chunk_index": 0,
                },
            }
        ]

        with patch.object(vector_store_module.settings, "qdrant_collection", collection_name):
            store.recreate_collection()
            store.upload_documents(first_documents, [[1.0, 0.0]])

            first_count = local_qdrant.count(collection_name, exact=True).count
            self.assertEqual(first_count, 1)

            store.recreate_collection()
            store.upload_documents(second_documents, [[0.0, 1.0]])

            second_count = local_qdrant.count(collection_name, exact=True).count
            self.assertEqual(second_count, 1)

            points, _ = local_qdrant.scroll(collection_name, limit=10)
            self.assertEqual(len(points), 1)
            self.assertEqual(points[0].payload["text"], "new chunk")
            self.assertEqual(points[0].payload["source"], "new.txt")


if __name__ == "__main__":
    unittest.main()
