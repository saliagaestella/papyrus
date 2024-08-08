from datetime import date, datetime
import os

from src.etls.boa.scrapper import BOAScrapper
from src.etls.common.utils import TextLoader
from src.etls.utils import catch_exceptions


@catch_exceptions(cancel_on_failure=True)
def today_boa():
    boa_scrapper = BOAScrapper()
    day = date.today()
    docs = boa_scrapper.download_day(day)
    documents = {}
    for doc in docs:
        loader = TextLoader(file_path=doc.filepath, metadata=doc.dict())
        document = loader.load()
        documents[document[0].metadata["identificador"]] = document[0]
        os.remove(doc.filepath)

    return documents


"""def dates(date_start: str, date_end: str, init_objects=None):
    if init_objects is None:
        init_objects = initialize_app()
    etl_job = ETL(
        config_loader=init_objects.config_loader,
        vector_store=init_objects.vector_store[COLLECTION_NAME],
    )
    boa_scrapper = BOAScrapper()
    docs = boa_scrapper.download_days(
        date_start=datetime.strptime(date_start, "%Y/%m/%d").date(),
        date_end=datetime.strptime(date_end, "%Y/%m/%d").date(),
    )
    if docs:
        etl_job.run(docs)

    subject = "[BOA] Load ETL executed"
    send_email(init_objects.config_loader, subject, content)"""


if __name__ == "__main__":
    today_boa()
