import os
import sys
import warnings
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.getenv("PROJECT_PATH"))
from src.docs_processor.processor import DocumentProcessor
from src.etls.boe.load import dates, today
from src.etls.bocm.load import today_bocm
from src.initialize import Initializer
from src.email.email_sender import send_email
from src.database.upload_documents import upload_documents


def main():
    initializer = Initializer()
    # documents = today_bocm()
    # documents = dates(date_start="2024/06/01", date_end="2024/06/07")
    processor = DocumentProcessor(initializer=initializer)

    process_documents(documents=today(), processor=processor, initializer=initializer)
    process_documents(documents=today_bocm(), processor=processor, initializer=initializer)


def process_documents(documents, processor, initializer):
    results = {}

    if not documents:
        warnings.warn("No documents found to process.")
    else:
        for doc_id, document in documents.items():
            try:
                ai_result = processor.process_document(document.page_content)
                results[doc_id] = [document, ai_result]
            except Exception as e:
                print(f"Failed to process document {doc_id}: {e}")

    upload_documents(results, initializer)
    send_email(results)

    for result in results:
        print(result)


if __name__ == "__main__":
    main()
