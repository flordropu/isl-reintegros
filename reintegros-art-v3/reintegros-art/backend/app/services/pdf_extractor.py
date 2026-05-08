"""
Servicio de extracción de datos desde PDFs.

Estrategia:
1. Intenta extraer texto directo con pdfplumber.
2. Si el texto extraído es muy corto (PDF escaneado), recae en OCR con Tesseract.
3. Aplica heurísticas para detectar campos comunes de la plantilla de reintegros ISL:
   - Montos ($)
   - CUIL
   - CBU / Alias
   - Fechas
   - Tipo de reintegro detectado por keywords

La capa de IA queda preparada pero apagada (settings.AI_EXTRACTION_ENABLED=False).
"""
import re
from pathlib import Path
from typing import Any

import pdfplumber

from app.core.config import settings


# Umbral mínimo de caracteres para considerar que el PDF tiene texto extraíble
MIN_TEXT_THRESHOLD = 50


def extraer_pdf(ruta: str) -> dict[str, Any]:
    """
    Extrae texto y datos estructurados de un PDF.
    Retorna: {metodo, texto_extraido, paginas, datos_estructurados}
    """
    ruta_path = Path(ruta)
    if not ruta_path.exists():
        return _empty_result("archivo_no_encontrado")

    # 1) Intento con pdfplumber
    texto, paginas = _extraer_con_pdfplumber(ruta)
    metodo = "pdfplumber"

    # 2) Fallback a OCR si el texto es insuficiente
    if len(texto.strip()) < MIN_TEXT_THRESHOLD and settings.OCR_ENABLED:
        texto_ocr, paginas_ocr = _extraer_con_ocr(ruta)
        if len(texto_ocr.strip()) > len(texto.strip()):
            texto = texto_ocr
            paginas = paginas_ocr or paginas
            metodo = "ocr"

    # 3) Parsing heurístico de campos de la plantilla
    datos = _parsear_campos(texto)

    return {
        "metodo": metodo,
        "texto_extraido": texto,
        "paginas": paginas,
        "datos_estructurados": datos,
    }


def _empty_result(metodo: str) -> dict[str, Any]:
    return {
        "metodo": metodo,
        "texto_extraido": "",
        "paginas": 0,
        "datos_estructurados": {},
    }


def _extraer_con_pdfplumber(ruta: str) -> tuple[str, int]:
    try:
        with pdfplumber.open(ruta) as pdf:
            paginas = len(pdf.pages)
            partes = []
            for page in pdf.pages:
                t = page.extract_text() or ""
                partes.append(t)
            return "\n".join(partes), paginas
    except Exception:
        return "", 0


def _extraer_con_ocr(ruta: str) -> tuple[str, int]:
    """OCR con Tesseract. Solo se usa si pdfplumber no encontró texto."""
    try:
        import pytesseract
        from pdf2image import convert_from_path

        imagenes = convert_from_path(ruta, dpi=200)
        partes = []
        for img in imagenes:
            t = pytesseract.image_to_string(img, lang=settings.OCR_LANGUAGE)
            partes.append(t)
        return "\n".join(partes), len(imagenes)
    except Exception:
        # Si Tesseract no está instalado o falla, devolvemos vacío silenciosamente
        return "", 0


# ---------------- Parsing heurístico ----------------

REGEX_MONTO = re.compile(r"\$\s*([\d\.,]+)")
REGEX_CUIL = re.compile(r"\b(\d{2}[-\s]?\d{7,8}[-\s]?\d)\b")
REGEX_CBU = re.compile(r"\b(\d{22})\b")
REGEX_ALIAS = re.compile(r"alias[:\s/]+([A-Z][A-Z0-9\.\-_]{4,})", re.IGNORECASE)
REGEX_FECHA = re.compile(r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b")
REGEX_TELEFONO = re.compile(r"(?:\+?54\s?)?(?:11|15)?[\s\-]?\d{4}[\s\-]?\d{4}")

KEYWORDS_TIPO = {
    "traslado_remis": ["remis", "traslado en remis"],
    "traslado_transporte_publico": ["transporte público", "transporte publico", "colectivo", "subte"],
    "medicacion": ["medicación", "medicacion", "medicamento", "droga", "comprimido", "cápsula", "capsula"],
    "ortopedia": ["órtesis", "ortesis", "muleta", "bota walker", "walker", "ortopedia"],
    "prestacion_medica": ["prestación", "prestacion", "consulta", "estudio", "rehabilitación", "rehabilitacion"],
    "alojamiento": ["alojamiento", "hospedaje", "hotel"],
}


def _normalizar_monto(s: str) -> float | None:
    """Convierte '1.234,56' o '1,234.56' a float."""
    s = s.strip()
    if not s:
        return None
    # heurística: si tiene coma y punto, asumimos formato AR (1.234,56)
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        # solo coma → decimal AR
        s = s.replace(",", ".")
    # si solo punto, lo dejamos
    try:
        return float(s)
    except ValueError:
        return None


def _parsear_campos(texto: str) -> dict[str, Any]:
    """Aplica regex y keywords para detectar campos típicos de la plantilla ISL."""
    if not texto:
        return {}

    datos: dict[str, Any] = {}

    # Montos: tomamos los dos más relevantes (total ticket y a abonar)
    montos_raw = REGEX_MONTO.findall(texto)
    montos = [m for m in (_normalizar_monto(x) for x in montos_raw) if m is not None]
    if montos:
        datos["montos_detectados"] = montos
        # heurística: si encontramos "total ticket" cerca, lo asignamos
        m_total = _buscar_monto_cercano(texto, ["monto total ticket", "total ticket"])
        m_abonar = _buscar_monto_cercano(texto, ["monto a abonar", "a abonar"])
        if m_total is not None:
            datos["monto_total_ticket"] = m_total
        if m_abonar is not None:
            datos["monto_a_abonar"] = m_abonar

    # CUIL
    cuil_match = REGEX_CUIL.search(texto)
    if cuil_match:
        datos["cuil"] = re.sub(r"[\s]", "", cuil_match.group(1))

    # CBU
    cbu_match = REGEX_CBU.search(texto)
    if cbu_match:
        datos["cbu"] = cbu_match.group(1)

    # Alias
    alias_match = REGEX_ALIAS.search(texto)
    if alias_match:
        datos["alias_cbu"] = alias_match.group(1)

    # Teléfono
    tel_match = REGEX_TELEFONO.search(texto)
    if tel_match:
        datos["telefono"] = tel_match.group(0).strip()

    # Fechas
    fechas = REGEX_FECHA.findall(texto)
    if fechas:
        datos["fechas_detectadas"] = [f"{d}/{m}/{a}" for d, m, a in fechas[:10]]

    # Tipo de reintegro detectado
    texto_lower = texto.lower()
    tipo_detectado = None
    for tipo, palabras in KEYWORDS_TIPO.items():
        if any(p in texto_lower for p in palabras):
            tipo_detectado = tipo
            break
    if tipo_detectado:
        datos["tipo_reintegro_sugerido"] = tipo_detectado

    return datos


def _buscar_monto_cercano(texto: str, frases: list[str]) -> float | None:
    """Busca un monto que aparezca cerca de alguna de las frases dadas."""
    texto_lower = texto.lower()
    for frase in frases:
        idx = texto_lower.find(frase)
        if idx == -1:
            continue
        # ventana de 80 caracteres después de la frase
        ventana = texto[idx: idx + 80]
        m = REGEX_MONTO.search(ventana)
        if m:
            return _normalizar_monto(m.group(1))
    return None
