import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.getenv("PROJECT_PATH"))
from src.docs_processor.processor import DocumentProcessor
from src.etls.boe.load import today
from src.initialize import Initializer


def main():
    initializer = Initializer()
    documents = today()
    processor = DocumentProcessor(initializer=initializer)

    try:
        results = processor.process_document(next(iter(documents.values())).page_content)
    except StopIteration:
        print("No documents found.")
        results = None


    print(results)


if __name__ == "__main__":
    main()
