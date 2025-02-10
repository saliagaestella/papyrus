import os
import sys
import warnings
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.getenv("PROJECT_PATH"))

from src.docs_processor.processor import DocumentProcessor
from src.etls.boe.load import dates_boe
from src.etls.bocyl.load import dates_bocyl
from src.etls.bocm.load import dates_bocm
from src.etls.boa.load import dates_boa
from src.etls.boja.load import dates_boja
from src.etls.bopv.load import dates_bopv
from src.initialize import Initializer
from src.email.email_sender import send_email
from src.database.upload_documents import upload_documents


def download_dates():
    initializer = Initializer()

    processor = DocumentProcessor(initializer=initializer)
    date_start = "2025/01/20"
    date_end = "2025/01/30"

    """results_boe = process_documents(
        documents=dates_boe(date_start=date_start, date_end=date_end),
        processor=processor,
        initializer=initializer,
        collection_name="BOE",
    )"""
    results_bocyl = process_documents(
        documents=dates_bocyl(date_start=date_start, date_end=date_end),
        processor=processor,
        initializer=initializer,
        collection_name="BOCYL",
    )
    """results_bocm = process_documents(
        documents=dates_bocm(date_start=date_start, date_end=date_end),
        processor=processor,
        initializer=initializer,
        collection_name="BOCM",
    )
    results_boa = process_documents(
        documents=dates_boa(date_start=date_start, date_end=date_end),
        processor=processor,
        initializer=initializer,
        collection_name="BOA",
    )
    results_boja = process_documents(
        documents=dates_boja(date_start=date_start, date_end=date_end),
        processor=processor,
        initializer=initializer,
        collection_name="BOJA",
    )
    results_bopv = process_documents(
        documents=dates_bopv(date_start=date_start, date_end=date_end),
        processor=processor,
        initializer=initializer,
        collection_name="BOPV",
    )

    results_joined = (
        results_boe | results_bocm | results_boa | results_boja | results_bopv
    )"""

    results_joined = results_bocyl

    if not results_joined:
        return
    else:
        send_email(documents=results_joined, dates=f"{date_start} - {date_end}")


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
            name = document.metadata["titulo"]
        except:
            name = None
        """try:
            ai_result = processor.process_document(
                text=document.page_content, name=name
            )
            results[doc_id] = [document, ai_result]
        except Exception as e:
            print(f"Failed to process document {doc_id}: {e}")"""
        ai_result = processor.process_document(text=document.page_content, name=name)
        results[doc_id] = [document, ai_result]

    if results:
        upload_documents(results, initializer)
        for result in results:
            print(result)
        return results


if __name__ == "__main__":
    download_dates()
