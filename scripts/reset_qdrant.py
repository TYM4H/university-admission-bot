from app.core.config import settings
from app.rag.qdrant_client import qdrant_client

def main():
    qdrant_client.delete_collection(settings.qdrant_collection)
    print("Collection deleted")

if __name__ == "__main__":
    main()