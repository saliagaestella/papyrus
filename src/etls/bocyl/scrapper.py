# src/etls/bocyl/bocyl_scrapper.py
import logging as lg
import random
import tempfile
import time
import typing as tp
from datetime import date, datetime

from bs4 import BeautifulSoup
from pypdf import PdfReader
import requests
from requests.exceptions import HTTPError

from src.etls.bocyl.metadata import BOCYLMetadataDocument
from src.etls.common.scrapper import BaseScrapper
from src.etls.utils import create_retry_session  # Assuming you have this utility


def _extract_metadata(soup: BeautifulSoup, url_html: str) -> tp.Dict:
    """Extracts metadata from the HTML content of a BOCYL disposición."""
    metadata_dict = {}

    # Extract title
    title_element = soup.find("p", class_="entradilla")  # Adjust the selector as needed
    if title_element:
        metadata_dict["titulo"] = title_element.get_text(strip=True)
    else:
        metadata_dict["titulo"] = "Título no encontrado"

    # Extract rango and departamento from h5 and h3 tags.
    h5_element = soup.find("h5")
    if h5_element:
        metadata_dict["departamento"] = h5_element.get_text(strip=True)
    else:
        metadata_dict["departamento"] = "Departamento no encontrado"

    h3_element = soup.find("h3")
    if h3_element:
        metadata_dict["rango"] = h3_element.get_text(strip=True)
    else:
        metadata_dict["rango"] = "Rango no encontrado"

    metadata_dict["url_html"] = url_html

    # Extract identificador from the <a> tag in the descargaBoletin class.
    descarga_boletin = soup.find("div", {"id": "resultados"})
    if descarga_boletin:
        a_tag = descarga_boletin.find(
            "a", href=True, title=lambda t: t and "pdf" in t.lower()
        )
        if a_tag:
            metadata_dict["url_pdf"] = (
                f"{a_tag['href']}"
            )
            parts = a_tag["href"].split("/")
            filename = parts[-1]  # Get the last part of the URL
            metadata_dict["identificador"] = filename.replace(".pdf", "")
            try:
                pdf = requests.get(metadata_dict["url_pdf"], headers={"Accept": "application/pdf"})
                with open("temp.pdf", "wb") as f:
                    f.write(pdf.content)
                with open("temp.pdf", "rb") as f:
                    reader = PdfReader(f)
                    num_paginas = len(reader.pages)
                    tiempo_lectura = round(num_paginas * 2.5)
                    metadata_dict["num_paginas"] = num_paginas
                    metadata_dict["tiempo_lectura"] = tiempo_lectura
            except:
                num_paginas = None
                tiempo_lectura = None
    else:
        metadata_dict["identificador"] = "Identificador no encontrado"
        metadata_dict["url_pdf"] = ""  # Or a placeholder value

    # Extract fecha_publicacion from the url_html AND populate anio, mes, dia
    try:
        parts = url_html.split("/")
        date_part = parts[-2]  # The part that looks like '20250210'
        metadata_dict["fecha_publicacion"] = datetime.strptime(
            date_part, "%Y%m%d"
        ).strftime(
            "%Y%m%d"
        )  # Keep the format consistent
        publication_date = datetime.strptime(date_part, "%Y%m%d")
        metadata_dict["anio"] = publication_date.strftime("%Y")
        metadata_dict["mes"] = publication_date.strftime("%m")
        metadata_dict["dia"] = publication_date.strftime("%d")

    except:
        metadata_dict["fecha_publicacion"] = ""
        metadata_dict["anio"] = ""
        metadata_dict["mes"] = ""
        metadata_dict["dia"] = ""

    return metadata_dict


class BOCYLScrapper(BaseScrapper):

    def download_day(self, day: date) -> tp.List[BOCYLMetadataDocument]:
        """Downloads all Disposiciones Generales for a specific date from BOCYL."""
        logger = lg.getLogger(self.download_day.__name__)
        logger.info("Downloading BOCYL content for day %s", day)

        date_str = day.strftime("%d/%m/%Y")
        summary_url = f"https://bocyl.jcyl.es/boletin.do?fechaBoletin={date_str}"
        metadata_documents = []

        try:
            session = create_retry_session(
                retries=3
            )  # Reduced retries since individual pages will also have retry logic.
            response = session.get(summary_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Find the "Disposiciones Generales" section
            seccion_heading = soup.find(
                "h4",
                {"class": "encabezado4_sinlinea", "id": "I.A._DISPOSICIONES_GENERALES"},
            )

            if not seccion_heading:
                logger.warning(
                    "No 'Disposiciones Generales' section found on %s", summary_url
                )
                return []  # Return an empty list, not None.

            # Find all the following <h5 class="encabezado6"> tags until the next h4 tag
            for element in seccion_heading.find_next_siblings():
                if element.name == "h4":  # Stop when you reach the next h4 (section)
                    break
                if (
                    element.name == "h5"
                    and element.has_attr("class")
                    and element["class"][0] == "encabezado6"
                ):
                    # Extract title from the following <p> tag
                    p_tag = element.find_next_sibling("p")
                    if p_tag:
                        title = p_tag.get_text(strip=True)

                        # Extract the link from the <a> tag inside the <ul> with class "descargaBoletin"
                        ul_tag = p_tag.find_next_sibling(
                            "ul", {"class": "descargaBoletin"}
                        )
                        if ul_tag:
                            # Look for the link to the HTML version.
                            a_tag = ul_tag.find(
                                "a",
                                href=True,
                                title=lambda t: t and "html" in t.lower(),
                            )  # Find the <a> tag whose title contains "html"
                            if a_tag:
                                url_html = a_tag["href"]
                                # Make the link absolute if it's relative
                                if not url_html.startswith("http"):
                                    url_html = f"https://bocyl.jcyl.es/{url_html}"

                                try:
                                    metadata_doc = self.download_document(url_html, day)
                                    metadata_documents.append(metadata_doc)
                                except HTTPError as e:
                                    logger.error(
                                        f"HTTPError while downloading document from {url_html}: {e}"
                                    )
                                except Exception as e:
                                    logger.exception(
                                        f"Exception while downloading document from {url_html}: {e}"
                                    )

        except HTTPError as e:
            logger.error(
                "HTTPError while downloading summary page %s: %s", summary_url, e
            )
        except Exception as e:
            logger.exception(
                "Exception while downloading summary page %s: %s", summary_url, e
            )

        logger.info(
            "Downloaded BOCYL content for day %s (%s documents)",
            day,
            len(metadata_documents),
        )
        return metadata_documents

    def download_document(self, url_html: str, day: date) -> BOCYLMetadataDocument:
        """Downloads the text content and metadata from a BOCYL disposición HTML page."""
        logger = lg.getLogger(self.download_document.__name__)
        logger.info("Downloading BOCYL document: %s", url_html)

        session = create_retry_session(
            retries=5
        )  # More retries for individual documents.
        try:
            response = session.get(url_html, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract the text content from the <div class="disposicion">
            disposicion_div = soup.find("div", class_="disposicion")
            if not disposicion_div:
                raise ValueError(
                    f"Could not find <div class='disposicion'> in {url_html}"
                )  # Raise an exception to be caught.

            paragraphs = disposicion_div.find_all("p")
            text_content = "\n".join(
                p.get_text(strip=True) for p in paragraphs
            )  # Join all paragraphs with a new line.

            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as fn:
                fn.write(text_content)

            metadata = _extract_metadata(soup, url_html)
            metadata_doc = BOCYLMetadataDocument(filepath=fn.name, **metadata)

            logger.info("Downloaded BOCYL document successfully: %s", url_html)
            return metadata_doc

        except HTTPError as e:
            logger.error("HTTPError while downloading %s: %s", url_html, e)
            raise  # Re-raise the exception so the calling function knows about the failure
        except ValueError as e:
            logger.error("ValueError while processing %s: %s", url_html, e)
            raise
        except Exception as e:
            logger.exception("Exception while processing %s: %s", url_html, e)
            raise  # Re-raise so that it's caught in download_day.
