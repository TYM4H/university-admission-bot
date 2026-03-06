from app.rag.retriever import retriever


def main():
    query = "Сколько действует ЕГЭ?"

    results = retriever.search(query)

    print(f"Query: {query}")
    print(f"Results found: {len(results)}")
    print()

    for index, result in enumerate(results, start=1):
        print(f"Result #{index}")
        print(f"Score: {result['score']}")
        print(f"Source: {result['source']}")
        print(f"Page: {result['page']}")
        print(f"Chunk: {result['chunk_index']}")
        print(result["text"][:700])
        print("-" * 80)


if __name__ == "__main__":
    main()