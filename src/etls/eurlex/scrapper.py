# src/etls/eurlex/eurlex_scrapper.py
import logging as lg
import tempfile
import time
import typing as tp
from datetime import date, datetime
from pypdf import PdfReader
import requests
from bs4 import BeautifulSoup
import os

from src.etls.eurlex.metadata import EurlexMetadataDocument
from src.etls.common.scrapper import BaseScrapper
from src.etls.utils import create_retry_session  # Assuming you have this utility

# EUR-Lex Search URL
EURLEX_DAILY_VIEW_URL = "https://eur-lex.europa.eu/oj/daily-view/L-series/default.html"


def _extract_text_from_html(html_content: str) -> str:
    """Extracts the main text content from EUR-Lex HTML using BeautifulSoup."""
    soup = BeautifulSoup(html_content, "html.parser")
    # Adapt the following selector based on EUR-Lex's actual HTML structure
    main_content_div = soup.find("div", id="MainContent")
    if main_content_div:
        return main_content_div.get_text(separator="\n", strip=True)
    else:
        return "Main content not found"


class EurlexScrapper(BaseScrapper):
    def __init__(self):
        self.language = "ES"  # Language of the documents

    def download_day(self, day: date) -> tp.List[EurlexMetadataDocument]:
        """Downloads all Regulation documents for a specific date from EUR-Lex by scraping the daily view."""
        logger = lg.getLogger(self.download_day.__name__)
        logger.info(
            "Downloading EUR-Lex Regulation documents for day %s by scraping daily view",
            day,
        )

        date_str = day.strftime("%d%m%Y")
        daily_view_url = f"{EURLEX_DAILY_VIEW_URL}?ojDate={date_str}&locale=es"
        metadata_documents = []

        try:
            session = create_retry_session(retries=3)
            response = session.get(daily_view_url, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Find all links to legal content documents.
            links = [
                a
                for a in soup.find_all("a", href=True)
                if "legal-content" in a["href"] and "TXT/?" in a["href"]
            ]  # Filter the results to get desired URLs.

            for a_tag in links:
                try:
                    url_html = f"https://eur-lex.europa.eu/{a_tag['href']}"  # Creating absolute URL
                    url_pdf = url_html.replace("TXT/", "TXT/PDF/")
                    try:
                        pdf = requests.get(
                            url_pdf, headers={"Accept": "application/pdf"}
                        )
                        with open("temp.pdf", "wb") as f:
                            f.write(pdf.content)
                        with open("temp.pdf", "rb") as f:
                            reader = PdfReader(f)
                            num_paginas = len(reader.pages)
                            tiempo_lectura = round(num_paginas * 2.5)
                    except:
                        num_paginas = None
                        tiempo_lectura = None

                    titulo = a_tag.get_text(strip=True)

                    rango = self._determinar_rango(titulo)

                    celex_id = self._extract_celex_id(url_html)

                    metadata_doc = self.download_document(
                        titulo=titulo,
                        url_html=url_html,
                        celex_id=celex_id,
                        day=day,
                        url_pdf=url_pdf,
                        num_paginas=num_paginas,
                        tiempo_lectura=tiempo_lectura,
                        rango=rango,
                    )

                    metadata_documents.append(metadata_doc)

                except Exception as e:
                    logger.exception(f"Error processing link {a_tag}: {e}")

                time.sleep(
                    5
                )  # Be respectful and abide to possible throttling policies.

        except requests.HTTPError as e:
            logger.error("HTTPError while querying daily view URL: %s", e)
        except Exception as e:
            logger.exception("Exception while querying daily view URL: %s", e)

        logger.info(
            "Downloaded EUR-Lex content for day %s (%s documents)",
            day,
            len(metadata_documents),
        )
        return metadata_documents

    def _extract_celex_id(self, url):
        """Extracts the CELEX ID from a EUR-Lex URL. Example https://eur-lex.europa.eu/legal-content/ES/TXT/?uri=OJ:L_202500318"""
        try:
            parts = url.split("OJ:")
            return parts[1]
        except:
            return ""  # If there is any error

    def _determinar_rango(self, titulo):
        # Normalize the titulo string
        titulo = titulo.lower()

        # Define the conditions for each rango
        if "reglam" in titulo:
            return "reglamento"
        elif "directiv" in titulo:
            return "directiva"
        elif "decision" in titulo or "decisión" in titulo:
            return "decision"
        elif "recomendacion" in titulo or "recomendación" in titulo:
            return "recomendacion"
        elif "dictamen" in titulo:
            return "dictamen"
        elif "resolucion" in titulo or "resolución" in titulo:
            return "resolucion"
        elif "declaracion" in titulo or "declaración" in titulo:
            return "declaracion"
        elif "acuerdo" in titulo:
            return "acuerdo"
        elif "presupuesto" in titulo:
            return "presupuesto"
        elif "posicion" in titulo or "posición" in titulo:
            return "posicion"
        elif "cooperacion" in titulo or "cooperación" in titulo:
            return "cooperacion"
        elif "no oposicion" in titulo or "no oposición" in titulo:
            return "no oposicion"
        elif "directriz" in titulo:
            return "directriz"
        elif "otros documentos" in titulo:
            return "otros documentos"
        else:
            return "desconocido"

    def download_document(
        self,
        titulo: str,
        url_html: str,
        celex_id: str,
        day: date,
        url_pdf: str,
        num_paginas: int,
        tiempo_lectura: int,
        rango: str,
    ) -> EurlexMetadataDocument:
        """Downloads the text content and metadata from a EUR-Lex document."""
        logger = lg.getLogger(self.download_document.__name__)
        logger.info(
            f"Downloading EUR-Lex document: CELEX ID: {celex_id}, Title: {titulo}"
        )

        try:
            session = create_retry_session(retries=5)
            response = session.get(url_html, timeout=30)  # Increased timeout
            response.raise_for_status()  # Raise HTTPError for bad responses
            html_content = response.text
            text_content = _extract_text_from_html(html_content)

            parts = celex_id.split("/")
            celex_year = parts[0][1:5]
            celex_month = parts[0][5:7]
            celex_day = parts[0][7:9]

            metadata = {
                "identificador": celex_id,  # We assign the CELEX as identifier
                "titulo": titulo,
                "date_document": day.strftime("%Y%m%d"),
                "rango": "",  # The API does not provide the document type. It would need an extra call
                "url_html": url_html,
                "anio": celex_year,
                "mes": celex_month,
                "dia": celex_day,
                "url_pdf": url_pdf,
                "num_paginas": num_paginas,
                "tiempo_lectura": tiempo_lectura,
                "rango": rango,
            }

            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as fn:
                fn.write(text_content)

            metadata_doc = EurlexMetadataDocument(filepath=fn.name, **metadata)
            logger.info(
                f"Downloaded and processed EUR-Lex document successfully: {celex_id}"
            )
            return metadata_doc

        except requests.HTTPError as e:
            logger.error("HTTPError while downloading %s: %s", url_html, e)
            raise  # Re-raise the exception so the calling function knows about the failure
        except ValueError as e:
            logger.error("ValueError while processing %s: %s", url_html, e)
            raise
        except Exception as e:
            logger.exception("Exception while processing %s: %s", url_html, e)
            raise  # Re-raise so that it's caught in download_day.
