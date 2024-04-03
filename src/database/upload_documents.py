from src.initialize import Initializer
from datetime import datetime
import json
from pymongo.errors import DuplicateKeyError


def convert_to_numeric(value):
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def upload_documents(docs: dict, initializer: Initializer):
    client = initializer.mongodb_client

    db = client["papyrus"]
    collection = db["BOE"]

    for doc_id, values in docs.items():
        element = {}
        metadata = values[0].metadata
        results = values[1]

        for key, value in metadata.items():
            if key == "identificador":
                key = "_id"
            elif (
                key in ["fecha_publicacion", "fecha_disposicion", "datetime_insert"]
                and value
            ):
                try:
                    element[key] = datetime.strptime(
                        value.split("T")[0], "%Y-%m-%d"
                    ).date()
                except ValueError:
                    print(
                        f"Could not convert date to datetime format for {key}: {value}"
                    )

            elif key == "ref_anteriores":
                value = [json.loads(ref) for ref in value]
            elif isinstance(value, str) and value.isdigit():
                value = convert_to_numeric(value)
            element[key] = value

        for key, value in results.items():
            if key == "resumenes":
                key = "resumen"
            element[key] = value

        try:
            collection.insert_one(element)
            print("Document uploaded to database successfully")
        except DuplicateKeyError:
            print(f"Document with _id {doc_id} already exists. Skipping")

    return 0
