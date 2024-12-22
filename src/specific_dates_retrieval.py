import os
import sys
import warnings
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.getenv("PROJECT_PATH"))

from src.docs_processor.processor import DocumentProcessor
from src.etls.boe.load import dates_boe, today_boe
from src.etls.bocm.load import today_bocm
from src.etls.boa.load import today_boa
from src.etls.boja.load import today_boja
from src.etls.bopv.load import today_bopv
from src.initialize import Initializer
from src.email.email_sender import send_email
from src.database.upload_documents import upload_documents


def download_dates():
    initializer = Initializer()
    processor = DocumentProcessor(initializer=initializer)

    results_boe = process_documents(
        documents=dates_boe(date_start="2024/12/21", date_end="2024/12/21"),
        processor=processor,
        initializer=initializer,
        collection_name="BOE",
    )
    """
    results_bocm = process_documents(
        documents=today_bocm(),
        processor=processor,
        initializer=initializer,
        collection_name="BOCM",
    )
    results_boa = process_documents(
        documents=today_boa(),
        processor=processor,
        initializer=initializer,
        collection_name="BOA",
    )
    results_boja = process_documents(
        documents=today_boja(),
        processor=processor,
        initializer=initializer,
        collection_name="BOJA",
    )
    results_bopv = process_documents(
        documents=today_bopv(),
        processor=processor,
        initializer=initializer,
        collection_name="BOPV",
    )

    results_joined = (
        results_boe | results_bocm | results_boa | results_boja | results_bopv
    )"""

    results_joined = results_boe

    if not results_joined:
        return
    else:
        send_email(results_joined, "TODO")


def process_documents(documents, processor, initializer, collection_name):
    results = {}

    client = initializer.mongodb_client
    db = client["papyrus"]
    collection = db[collection_name]

    ids_to_insert = list(documents.keys())
    existing_docs = collection.find({"_id": {"$in": ids_to_insert}}, {"_id": 1})
    existing_ids_set = {doc["_id"] for doc in existing_docs}

    new_documents = {
        doc_id: document
        for doc_id, document in documents.items()
        if doc_id not in existing_ids_set
    }

    if not new_documents:
        warnings.warn(
            f"No new documents found to process for collection {collection_name}."
        )
        return {}

    for doc_id, document in new_documents.items():
        try:
            ai_result = processor.process_document(document.page_content)
            results[doc_id] = [document, ai_result]
        except Exception as e:
            print(f"Failed to process document {doc_id}: {e}")

    if results:
        upload_documents(results, initializer)
        for result in results:
            print(result)
        return results


if __name__ == "__main__":
    download_dates()
