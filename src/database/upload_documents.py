from src.initialize import Initializer
from datetime import datetime
import json


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
            elif key in ["fecha_publicacion", "fecha_disposicion", "datetime_insert"]:
                value = datetime.fromisoformat(value)
            elif key == "ref_anteriores":
                value = [json.loads(ref) for ref in value]
            elif isinstance(value, str) and value.isdigit():
                value = convert_to_numeric(value)
            element[key] = value

        for key, value in results.items():
            if key == "resumenes":
                key = "resumen"
            element[key] = value

        collection.insert_one(element)

    return 0