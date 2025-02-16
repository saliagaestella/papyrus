# src/etls/eurlex/eurlex_metadata.py
import typing as tp
from datetime import datetime

from pydantic import BaseModel, field_validator

from src.etls.common.metadata import MetadataDocument


class EurlexMetadataDocument(MetadataDocument):
    """Class for keeping metadata of a Eurlex Document from the Cellar API."""

    # Text
    filepath: str

    # Source
    source_name: str = "DOUE"  # Changed source name
    source_type: str = "Boletin"

    # Metadatos - Adapt these to the API's data structure
    identificador: str  # The CELEX identifier
    titulo: str
    date_document: str  # Publication date as YYYY-MM-DD
    rango: str = ""  # e.g., 'regulation', 'directive'
    author: str = ""  # Authoring institution.
    subject: tp.List[str] = []  # Subject matter list
    url_pdf: str
    url_html: str
    num_paginas: tp.Optional[int] = None
    tiempo_lectura: tp.Optional[int] = None

    # Optional/Less Common Metadata
    number_of_pages: int = 0
    legal_basis: str = ""
    case_law: str = ""  # Relevant case law

    # Analisis - Keeping these, even if not readily available, for consistency
    observaciones: str = ""
    ambito_geografico: str = "UE"
    modalidad: str = ""
    tipo: str = ""
    materias: tp.List[str] = []
    alertas: tp.List[str] = []
    notas: tp.List[str] = []

    datetime_insert: str = datetime.utcnow().isoformat()

    @field_validator("date_document")
    @classmethod
    def isoformat(cls, v):
        if v:
            return datetime.strptime(v, "%Y%m%d").strftime("%Y-%m-%d")
        return v
