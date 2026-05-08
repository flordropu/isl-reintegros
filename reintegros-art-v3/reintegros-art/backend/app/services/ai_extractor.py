"""
Servicio de extracción asistida por IA.

Estado actual: DESHABILITADO por defecto (settings.AI_EXTRACTION_ENABLED=False).

Cuando se habilite, esta capa puede usar la API de Anthropic para extraer
datos estructurados desde el texto de un PDF con mucha más precisión que las
heurísticas regex actuales.

Para activar:
1. Setear ANTHROPIC_API_KEY en .env
2. Setear AI_EXTRACTION_ENABLED=True
3. Instalar el SDK: pip install anthropic
4. Implementar la llamada en _extraer_con_ia()
"""
from typing import Any
from app.core.config import settings


def extraer_con_ia(texto: str, tipo_reintegro: str | None = None) -> dict[str, Any] | None:
    """
    Devuelve datos estructurados extraídos por IA, o None si está deshabilitado.

    El frontend puede usar esto para auto-completar formularios con mayor precisión
    que la regex de pdf_extractor.
    """
    if not settings.AI_EXTRACTION_ENABLED:
        return None
    if not settings.ANTHROPIC_API_KEY:
        return None
    return _extraer_con_ia(texto, tipo_reintegro)


def _extraer_con_ia(texto: str, tipo_reintegro: str | None) -> dict[str, Any]:
    """
    TODO: Implementación real cuando se active.

    Esquema sugerido:

        from anthropic import Anthropic
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        prompt = f'''
        Extraé los siguientes campos del texto de un comprobante de reintegro ART.
        Devolvé SOLO un JSON válido con las claves:
        - monto_total_ticket (number)
        - monto_a_abonar (number)
        - cuil (string)
        - cbu (string)
        - alias_cbu (string)
        - fechas (array of strings YYYY-MM-DD)
        - origen (string, solo si es traslado)
        - destino (string, solo si es traslado)
        - cantidad_viajes (number, solo si es traslado)
        - medicamentos (array, solo si es medicación)

        Tipo esperado: {tipo_reintegro or "desconocido"}

        TEXTO:
        {texto}
        '''

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        return json.loads(response.content[0].text)
    """
    return {}
