"""Utilidades de texto reutilizables."""

import re
import unicodedata


def slugify(value: str) -> str:
    """Convierte un texto en un slug apto para URL.

    Normaliza acentos (por ejemplo, "Café" -> "cafe"), reemplaza cualquier
    secuencia de caracteres no alfanuméricos por guiones y pasa a minúsculas.

    Args:
        value: Texto de origen.

    Returns:
        Un slug en minúsculas. Si el resultado queda vacío, usa "negocio".
    """
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return slug or "negocio"
