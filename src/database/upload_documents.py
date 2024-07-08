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

    for doc_id, values in docs.items():
        element = {}
        metadata = values[0].metadata
        results = values[1]
        collection = db[metadata["source_name"]]

        for key, value in metadata.items():
            if key == "identificador":
                key = "_id"
            elif (
                key in ["fecha_publicacion", "fecha_disposicion", "datetime_insert"]
                and value
            ):
                try:
                    date = datetime.strptime(value.split("T")[0], "%Y-%m-%d").date()
                    value = datetime.combine(date, datetime.min.time())
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
            print(f"Document with id {doc_id} uploaded to database successfully")
        except DuplicateKeyError:
            print(f"Document with id {doc_id} already exists - skipping")

    return 0
