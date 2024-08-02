from datetime import date, datetime
import os

from src.etls.bocm.scrapper import BOCMScrapper
from src.etls.utils import catch_exceptions
from src.etls.bocm.defs import COLLECTION_NAME
from src.etls.common.utils import TextLoader


@catch_exceptions(cancel_on_failure=True)
def today_bocm():
    bocm_scrapper = BOCMScrapper()
    day = date.today()
    docs = bocm_scrapper.download_day(day)
    documents = {}
    for doc in docs:
        loader = TextLoader(file_path=doc.filepath, metadata=doc.dict())
        document = loader.load()
        documents[document.metadata["identificador"]] = document
        os.remove(doc.filepath)

    return documents


"""def dates(date_start: str, date_end: str, init_objects=None):
    if init_objects is None:
        init_objects = initialize_app()
    etl_job = ETL(config_loader=init_objects.config_loader, vector_store=init_objects.vector_store[COLLECTION_NAME])
    bocm_scrapper = BOCMScrapper()
    docs = bocm_scrapper.download_days(
        date_start=datetime.strptime(date_start, "%Y/%m/%d").date(),
        date_end=datetime.strptime(date_end, "%Y/%m/%d").date(),
    )
    if docs:
        etl_job.run(docs)"""
