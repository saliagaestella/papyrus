import sys


sys.path.append("/Users/santiago/Documents/papyrus")
from src.docs_processor.processor import DocumentProcessor
from src.etls.boe.load import today
from src.initialize import Initializer


def main():
    initializer = Initializer()

    processor = DocumentProcessor(initializer=initializer)

    documents = today()

    try:
        results = processor.process_document(next(iter(documents.values())).page_content)
    except StopIteration:
        print("No documents found.")
        results = None


    print(results)


if __name__ == "__main__":
    main()
