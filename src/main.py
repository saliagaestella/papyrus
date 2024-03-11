import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.getenv("PROJECT_PATH"))
from src.docs_processor.processor import DocumentProcessor
from src.etls.boe.load import today
from src.initialize import Initializer
from src.email.email_sender import send_email


def main():
    initializer = Initializer()
    documents = today()
    processor = DocumentProcessor(initializer=initializer)

    results = {}

    if not documents:
        print("No documents found.")
    else:
        for doc_id, document in documents.items():
            try:
                ai_result = processor.process_document(document.page_content)
                results[doc_id] = [document, ai_result]
            except Exception as e:
                print(f"Failed to process document {doc_id}: {e}")

    send_email(results)

    for result in results:
        print(result)


if __name__ == "__main__":
    main()
