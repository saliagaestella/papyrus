# src/etls/boe/load.py (Modified)
from datetime import date, datetime, timedelta
import os
import logging as lg

from src.etls.boe.scrapper import BOEScrapper
from src.etls.bocyl.scrapper import BOCYLScrapper  # Import BOCYLScrapper
from src.etls.common.utils import TextLoader


def today_boe():
    boe_scrapper = BOEScrapper()
    day = date.today()
    docs = boe_scrapper.download_day(day)
    documents = {}
    for doc in docs:
        loader = TextLoader(file_path=doc.filepath, metadata=doc.dict())
        document = loader.load()
        documents[document[0].metadata["identificador"]] = document[0]
        os.remove(doc.filepath)

    return documents


def dates_boe(date_start: str, date_end: str):
    boe_scrapper = BOEScrapper()
    docs = boe_scrapper.download_days(
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


def today_bocyl():
    """Downloads and loads BOCYL documents for today's date."""
    logger = lg.getLogger(today_bocyl.__name__)
    bocyl_scrapper = BOCYLScrapper()
    day = date.today()
    docs = bocyl_scrapper.download_day(day)
    documents = {}
    for doc in docs:
        try:
            loader = TextLoader(file_path=doc.filepath, metadata=doc.dict())
            document = loader.load()
            documents[document[0].metadata["identificador"]] = document[0]
        except Exception as e:
            logger.error(f"Error loading document {doc.filepath}: {e}")
        finally:
            try:
                os.remove(doc.filepath)  # Clean up the temporary file
            except OSError as e:
                logger.warning(f"Could not remove temporary file {doc.filepath}: {e}")
    return documents


def dates_bocyl(date_start: str, date_end: str):
    """Downloads and loads BOCYL documents for a range of dates."""
    logger = lg.getLogger(dates_bocyl.__name__)
    bocyl_scrapper = BOCYLScrapper()
    start_date = datetime.strptime(date_start, "%Y/%m/%d").date()
    end_date = datetime.strptime(date_end, "%Y/%m/%d").date()
    documents = {}

    current_date = start_date
    while current_date <= end_date:
        docs = bocyl_scrapper.download_day(current_date)
        for doc in docs:
            try:
                loader = TextLoader(file_path=doc.filepath, metadata=doc.dict())
                document = loader.load()
                documents[document[0].metadata["identificador"]] = document[0]
            except Exception as e:
                logger.error(f"Error loading document {doc.filepath}: {e}")
            finally:
                try:
                    os.remove(doc.filepath)  # Clean up the temporary file
                except OSError as e:
                    logger.warning(f"Could not remove temporary file {doc.filepath}: {e}")
        current_date += timedelta(days=1)  # Increment to the next day

    return documents


if __name__ == "__main__":
    #Example usage
    #today_bocyl() #This will get files from today
    documents = dates_bocyl(date_start="2025/02/10", date_end="2025/02/10")

    #Print keys and title for the dispositions found.
    for key, value in documents.items():
        print(f"Key: {key}, Title: {value.metadata['titulo']}")