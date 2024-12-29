import logging as lg
import random
import tempfile
import time
import typing as tp
from datetime import date, datetime

from bs4 import BeautifulSoup
import requests
from requests.exceptions import HTTPError
from pypdf import PdfReader

from src.etls.boe.metadata import BOEMetadataDocument, BOEMetadataReferencia
from src.etls.common.scrapper import BaseScrapper
from src.etls.utils import create_retry_session


def _extract_metadata(soup) -> tp.Dict:
    metadata_dict = {}

    # Metadatos
    if identificador := soup.documento.metadatos.identificador:
        metadata_dict["identificador"] = identificador.get_text()
        metadata_dict["url_html"] = (
            f"https://www.boe.es/diario_boe/txt.php?id={identificador.get_text()}"
        )

    if diario := soup.documento.metadatos.diario:
        metadata_dict["diario"] = diario.get_text()

    if numero_oficial := soup.documento.metadatos.numero_oficial:
        metadata_dict["numero_oficial"] = numero_oficial.get_text()

    if departamento := soup.documento.metadatos.departamento:
        metadata_dict["departamento"] = departamento.get_text()

    if rango := soup.documento.metadatos.rango:
        metadata_dict["rango"] = rango.get_text()

    if titulo := soup.documento.metadatos.titulo:
        metadata_dict["titulo"] = titulo.get_text()

    if url_pdf := soup.documento.metadatos.url_pdf:
        url = f"https://www.boe.es{url_pdf.get_text()}"
        metadata_dict["url_pdf"] = url

        pdf = requests.get(url, headers={"Accept": "application/pdf"})
        with open("temp.pdf", "wb") as f:
            f.write(pdf.content)
        with open("temp.pdf", "rb") as f:
            reader = PdfReader(f)
            num_paginas = len(reader.pages)
            metadata_dict["num_paginas"] = num_paginas
            metadata_dict["tiempo_lectura"] = round(num_paginas * 2.5)

    if origen_legislativo := soup.documento.metadatos.origen_legislativo:
        metadata_dict["origen_legislativo"] = origen_legislativo.get_text()

    if fecha_publicacion := soup.documento.metadatos.fecha_publicacion:
        metadata_dict["fecha_publicacion"] = fecha_publicacion.get_text()

    if fecha_disposicion := soup.documento.metadatos.fecha_disposicion:
        metadata_dict["fecha_disposicion"] = fecha_disposicion.get_text()

    if fecha_vigencia := soup.documento.metadatos.fecha_vigencia:
        metadata_dict["fecha_vigencia"] = fecha_vigencia.get_text()

    metadata_dict["anio"] = datetime.strptime(
        fecha_publicacion.get_text(), "%Y%m%d"
    ).strftime("%Y")

    metadata_dict["mes"] = datetime.strptime(
        fecha_publicacion.get_text(), "%Y%m%d"
    ).strftime("%m")

    metadata_dict["dia"] = datetime.strptime(
        fecha_publicacion.get_text(), "%Y%m%d"
    ).strftime("%d")

    # Analisis
    if observaciones := soup.documento.analisis.observaciones:
        metadata_dict["observaciones"] = observaciones.get_text()

    if ambito_geografico := soup.documento.analisis.ambito_geografico:
        metadata_dict["ambito_geografico"] = ambito_geografico.get_text()

    if modalidad := soup.documento.analisis.modalidad:
        metadata_dict["modalidad"] = modalidad.get_text()

    if tipo := soup.documento.analisis.tipo:
        metadata_dict["tipo"] = tipo.get_text()

    metadata_dict["materias"] = [
        materia.get_text()
        for materia in soup.select("documento > analisis > materias > materia")
    ]
    metadata_dict["alertas"] = [
        alerta.get_text()
        for alerta in soup.select("documento > analisis > alertas > alerta")
    ]
    metadata_dict["notas"] = [
        nota.get_text() for nota in soup.select("documento > analisis > notas > nota")
    ]
    metadata_dict["ref_posteriores"] = [
        BOEMetadataReferencia(
            id=ref["referencia"],
            palabra=ref.palabra.get_text(),
            texto=ref.texto.get_text(),
        )
        for ref in soup.select(
            "documento > analisis > referencias > posteriores > posterior"
        )
    ]
    metadata_dict["ref_anteriores"] = [
        BOEMetadataReferencia(
            id=ref["referencia"],
            palabra=ref.palabra.get_text(),
            texto=ref.texto.get_text(),
        )
        for ref in soup.select(
            "documento > analisis > referencias > anteriores > anterior"
        )
    ]
    return metadata_dict


def _list_links_day(day_url: str, content: str) -> tp.List[str]:
    """Get a list of links in a BOE url day filtering by Seccion 1 and Seccion T.

    :param content: Content of the request. Example: https://www.boe.es/diario_boe/xml.php?id=BOE-S-20230817
    :return: list of id documents to explore (links)
    """
    logger = lg.getLogger(_list_links_day.__name__)
    logger.info("Scrapping day: %s", day_url)
    soup = BeautifulSoup(content, features="xml")
    id_links = [
        url.text.split("?id=")[-1]  # Extract the ID from the URL
        for section in soup.find_all(
            lambda tag: tag.name == "seccion"
            and "codigo" in tag.attrs
            and tag.attrs["codigo"]
            in ["1", "T"]  # Filter seccion 1 or Tribunal Supremo
        )
        for item in section.find_all("item")  # Go deeper into <item>
        for url in item.find_all("url_xml")  # Find <url_xml> inside <item>
    ]
    logger.info(
        "Scrapped day successfully %s (%s BOE documents)", day_url, len(id_links)
    )
    return id_links


class BOEScrapper(BaseScrapper):
    def download_day(self, day: date) -> tp.List[BOEMetadataDocument]:
        """Download all the documents for a specific date."""
        logger = lg.getLogger(self.download_day.__name__)
        logger.info("Downloading BOE content for day %s", day)
        day_str = day.strftime("%Y%m%d")
        day_url = f"https://www.boe.es/datosabiertos/api/boe/sumario/{day_str}"
        metadata_documents = []
        try:
            headers = {"Accept": "application/xml"}
            response = requests.get(day_url, headers=headers)
            response.raise_for_status()  # This will raise an HTTPError for bad responses
            id_links = _list_links_day(day_url, response.text)
            for id_link in id_links:
                url_document = f"https://www.boe.es/diario_boe/xml.php?id={id_link}"
                try:
                    metadata_doc = self.download_document(url_document)
                    metadata_documents.append(metadata_doc)
                except HTTPError as e:
                    logger.error(
                        "Not scrapped document %s on day %s. HTTPError: %s",
                        url_document,
                        day_url,
                        e,
                    )
                except AttributeError:
                    logger.error(
                        "Not scrapped document %s on day %s", url_document, day_url
                    )
        except HTTPError as e:
            logger.error("Not scrapped document on day %s. HTTPError: %s", day_url, e)
            logger.error(
                "Status Code: %s, Response Content: %s",
                e.response.status_code,
                e.response.text,
            )
            print(e.response.status_code, e.response.text, e)
        logger.info("Downloaded BOE content for day %s", day)
        return metadata_documents

    def download_document(self, url: str) -> BOEMetadataDocument:
        """Get text and metadata from a BOE xml url document.

        :param url: document url link. Examples:
            * https://www.boe.es/diario_boe/xml.php?id=BOE-A-2022-14630
            * https://www.boe.es/diario_boe/xml.php?id=BOE-A-2023-12203
        :return: document with metadata and filepath with text content
        """
        logger = lg.getLogger(self.download_document.__name__)
        logger.info("Scrapping document: %s", url)
        session = create_retry_session(retries=10)
        response = session.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        with tempfile.NamedTemporaryFile("w", delete=False) as fn:
            text = soup.select_one("documento > texto").get_text()
            fn.write(text)
        metadata_doc = BOEMetadataDocument(filepath=fn.name, **_extract_metadata(soup))
        logger.info("Scrapped document successfully %s", url)
        return metadata_doc
