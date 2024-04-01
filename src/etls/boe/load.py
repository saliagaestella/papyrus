from datetime import date, datetime, timedelta
import os


from src.etls.boe.scrapper import BOEScrapper
from src.etls.common.utils import TextLoader


def today():
    boe_scrapper = BOEScrapper()
    # TODO: Quitar
    day = date.today() - timedelta(days=5)
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


'''@app.command()
def dates(date_start: str, date_end: str, init_objects=None):
    if init_objects is None:
        init_objects = initialize_app()
    etl_job = ETL(config_loader=init_objects.config_loader, vector_store=init_objects.vector_store[COLLECTION_NAME])
    boe_scrapper = BOEScrapper()
    docs = boe_scrapper.download_days(
        date_start=datetime.strptime(date_start, "%Y/%m/%d").date(),
        date_end=datetime.strptime(date_end, "%Y/%m/%d").date(),
    )
    if docs:
        etl_job.run(docs)

    subject = "[BOE] Load ETL executed"
    content = f"""
    Load ETL executed
    - Date start: {date_start}
    - Date end: {date_end}
    - Documents loaded: {len(docs)} 
    - Database used: {init_objects.config_loader['vector_store']}
    """
    #send_email(init_objects.config_loader, subject, content)'''


if __name__ == "__main__":
    today()
