# src/etls/eurlex/load.py
from datetime import date, datetime, timedelta
import os
import logging as lg

from src.etls.eurlex.scrapper import EurlexScrapper  # Import EurlexScrapper
from src.etls.common.utils import TextLoader


def today_eurlex():
    """Downloads and loads EUR-Lex documents for today's date."""
    logger = lg.getLogger(today_eurlex.__name__)
    eurlex_scrapper = EurlexScrapper()
    day = date.today()
    docs = eurlex_scrapper.download_day(day)
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


def dates_eurlex(date_start: str, date_end: str):
    """Downloads and loads EUR-Lex documents for a range of dates."""
    logger = lg.getLogger(dates_eurlex.__name__)
    eurlex_scrapper = EurlexScrapper()
    start_date = datetime.strptime(date_start, "%Y/%m/%d").date()
    end_date = datetime.strptime(date_end, "%Y/%m/%d").date()
    documents = {}

    current_date = start_date
    while current_date <= end_date:
        docs = eurlex_scrapper.download_day(current_date)
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
    # Example usage:
    #today_eurlex() #This will get files from today
    documents = dates_eurlex(date_start="2025/02/14", date_end="2025/02/14") #Example date.
    for key, value in documents.items():
        print(f"Key: {key}, Title: {value.metadata['title']}, PDF URL: {value.metadata['url_pdf']}")