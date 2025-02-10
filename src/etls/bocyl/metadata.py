# src/etls/bocyl/bocyl_metadata.py
import typing as tp
from datetime import datetime

from pydantic import BaseModel, field_validator

from src.etls.common.metadata import MetadataDocument


class BOCYLMetadataDocument(MetadataDocument):
    """Class for keeping metadata of a BOCYL Document scrapped."""

    # Text
    filepath: str

    # Source
    source_name: str = "BOCYL"
    source_type: str = "Boletin"

    # Metadatos
    identificador: str # e.g., BOCYL-D-10022025-1
    diario: str = "Boletín Oficial de Castilla y León" # Fixed value
    numero_oficial: str = "" #Not available, can be empty
    departamento: str # e.g., CONSEJERÍA DE ECONOMÍA Y HACIENDA
    rango: str = ""  # e.g., DECRETO or ORDEN or RESOLUCION
    titulo: str  # e.g., DECRETO 2/2025, de 6 de febrero...
    url_pdf: str # URL to the PDF version
    url_html: str # URL to the HTML version
    origen_legislativo: str = "" #Not available
    fecha_publicacion: str #YYYY-MM-DD
    fecha_disposicion: str = "" #Not available
    fecha_vigencia: str = "" #Not available
    anio: str
    mes: str
    dia: str
    num_paginas: int = 0 # We can calculate this if we download the PDF.
    tiempo_lectura: int = 0 # We can calculate this if we download the PDF.

    # Analisis - Keeping these, even if not readily available, for consistency
    observaciones: str = ""
    ambito_geografico: str = "Castilla y León"
    modalidad: str = ""
    tipo: str = ""
    materias: tp.List[str] = []
    alertas: tp.List[str] = []
    notas: tp.List[str] = []

    datetime_insert: str = datetime.utcnow().isoformat()

    @field_validator("fecha_publicacion")
    @classmethod
    def isoformat(cls, v):
        if v:
            return datetime.strptime(v, "%Y%m%d").strftime("%Y-%m-%d")
        return v