from datetime import date
import os
import sys
import warnings
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.getenv("PROJECT_PATH"))

from src.docs_processor.processor import DocumentProcessor
from src.etls.boe.load import today_boe
from src.etls.bocm.load import today_bocm
from src.etls.boa.load import today_boa
from src.etls.boja.load import today_boja
from src.etls.bocyl.load import today_bocyl
from src.etls.bopv.load import today_bopv
from src.etls.eurlex.load import today_eurlex
from src.initialize import Initializer
from src.email.email_sender import send_email
from src.database.upload_documents import upload_documents


def main():
    initializer = Initializer()
    processor = DocumentProcessor(initializer=initializer)

    try:
        results_boe = process_documents(
            documents=today_boe(),
            processor=processor,
            initializer=initializer,
            collection_name="BOE",
        )
    except Exception as e:
        print(f"Failed to scrap BOE documents: {e}")
        results_boe = {}
    try:
        results_bocm = process_documents(
            documents=today_bocm(),
            processor=processor,
            initializer=initializer,
            collection_name="BOCM",
        )
    except Exception as e:
        print(f"Failed to scrap BOCM documents: {e}")
        results_bocm = {}
    try:
        results_boa = process_documents(
            documents=today_boa(),
            processor=processor,
            initializer=initializer,
            collection_name="BOA",
        )
    except Exception as e:
        print(f"Failed to scrap BOA documents: {e}")
        results_boa = {}
    try:
        results_boja = process_documents(
            documents=today_boja(),
            processor=processor,
            initializer=initializer,
            collection_name="BOJA",
        )
    except Exception as e:
        print(f"Failed to scrap BOJA documents: {e}")
        results_boja = {}
    try:
        results_bopv = process_documents(
            documents=today_bopv(),
            processor=processor,
            initializer=initializer,
            collection_name="BOPV",
        )
    except Exception as e:
        print(f"Failed to scrap BOPV documents: {e}")
        results_bopv = {}
    try:
        results_bocyl = process_documents(
            documents=today_bocyl(),
            processor=processor,
            initializer=initializer,
            collection_name="BOCYL",
        )
    except Exception as e:
        print(f"Failed to scrap BOCYL documents: {e}")
        results_bocyl = {}
    try:
        results_eurlex = process_documents(
            documents=today_eurlex(),
            processor=processor,
            initializer=initializer,
            collection_name="DOUE",
        )
    except Exception as e:
        print(f"Failed to scrap DOUE documents: {e}")
        results_eurlex = {}

    results_joined = (
        results_boe
        | results_bocm
        | results_boa
        | results_boja
        | results_bopv
        | results_bocyl
        | results_eurlex
    )

    if not results_joined:
        return
    else:
        send_email(documents=results_joined, dates=date.today())


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
        try:
            ai_result = processor.process_document(
                text=document.page_content, name=name
            )
            results[doc_id] = [document, ai_result]
        except Exception as e:
            print(f"Failed to process document {doc_id}: {e}")

    if results:
        upload_documents(results, initializer)
        for result in results:
            print(result)
        return results


if __name__ == "__main__":
    main()
