from datetime import date, datetime, timedelta
import os


from src.etls.boe.scrapper import BOEScrapper
from src.etls.common.utils import TextLoader


def today_boe():
    boe_scrapper = BOEScrapper()
    day = date.today()
    docs = boe_scrapper.download_day(day)
    documents = {}
    for doc in docs:
        loader = TextLoader(file_path=doc.filepath, metadata=doc.dict())
        document = loader.load()
        documents[document.metadata["identificador"]] = document
        os.remove(doc.filepath)

    return documents


def dates(date_start: str, date_end: str):
    boe_scrapper = BOEScrapper()
    docs = boe_scrapper.download_days(
        date_start=datetime.strptime(date_start, "%Y/%m/%d").date(),
        date_end=datetime.strptime(date_end, "%Y/%m/%d").date(),
    )
    documents = {}
    for doc in docs:
        loader = TextLoader(file_path=doc.filepath, metadata=doc.dict())
        document = loader.load()
        documents[document.metadata["identificador"]] = document
        os.remove(doc.filepath)

    return documents


if __name__ == "__main__":
    today()
