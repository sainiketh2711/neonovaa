from pathlib import Path

from knowledge_base import (
    build_knowledge_base,
    display_knowledge_base
)

from reasoning_engine import process_with_reasoning


def main():

    project_folder = Path(__file__).resolve().parent.parent

    document_path = (
        project_folder
        / "documents"
        / "library_guide.txt"
    )

    if not document_path.exists():
        print("ERROR: Library guide document was not found.")
        print(f"Expected location: {document_path}")
        return

    with open(
        document_path,
        "r",
        encoding="utf-8"
    ) as file:

        document_text = file.read()

    knowledge_base = build_knowledge_base(document_text)

    if not knowledge_base:
        print("ERROR: No information could be extracted.")
        print("Please check the document wording.")
        return

    print("\n" + "=" * 50)
    print("ADVANCED DOCUMENT QUESTION ANSWERING SYSTEM")
    print("=" * 50)

    print("\nDocument successfully loaded.")
    print("Knowledge Base successfully constructed.")

    display_knowledge_base(knowledge_base)

    print("\n" + "=" * 50)
    print("QUESTION ANSWERING SYSTEM")
    print("=" * 50)

    print("Ask one or more questions about the library.")
    print("Type 'exit' to stop.\n")

    while True:

        try:
            question = input("Enter your question: ").strip()

            if question.lower() == "exit":
                print("System closed.")
                break

            if not question:
                print("Please enter a question.\n")
                continue

            answer = process_with_reasoning(
                question,
                knowledge_base
            )

            print("\nAnswer:")
            print(answer)
            print()

        except KeyboardInterrupt:
            print("\nSystem closed.")
            break

        except Exception as error:
            print("\nAn unexpected error occurred:")
            print(error)
            print()


if __name__ == "__main__":
    main()