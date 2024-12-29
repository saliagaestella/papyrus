from datetime import date, datetime
import os


from src.etls.boja.scrapper import BOJAScrapper
from src.etls.common.utils import TextLoader
from src.etls.utils import catch_exceptions


@catch_exceptions(cancel_on_failure=True)
def today_boja():
    boja_scrapper = BOJAScrapper()
    day = date.today()
    docs = boja_scrapper.download_day(day)
    documents = {}
    for doc in docs:
        loader = TextLoader(file_path=doc.filepath, metadata=doc.dict())
        document = loader.load()
        documents[document[0].metadata["identificador"]] = document[0]
        os.remove(doc.filepath)

    return documents


def dates_boja(date_start: str, date_end: str):
    boja_scrapper = BOJAScrapper()
    docs = boja_scrapper.download_days(
        date_start=datetime.strptime(date_start, "%Y/%m/%d").date(),
        date_end=datetime.strptime(date_end, "%Y/%m/%d").date(),
    )
    documents = {}
    for doc in docs:
        loader = TextLoader(file_path=doc.filepath, metadata=doc.dict())
        document = loader.load()
        documents[document[0].metadata["identificador"]] = document[0]
        os.remove(doc.filepath)

    return documents


if __name__ == "__main__":
    dates_boja()
