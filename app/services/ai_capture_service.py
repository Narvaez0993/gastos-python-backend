
from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Any, List, Optional

import pytz
from anthropic import Anthropic, APIError, APITimeoutError
from fastapi import HTTPException

from app.config.settings import Settings
from app.repositories.interfaces.money_source_repository import IMoneySourceRepository
from app.schemas.capture import CaptureResponse, ParsedExpenseItem

DEFAULT_CATEGORIES = [
    "Comida",
    "Transporte",
    "Mercado",
    "Salud",
    "Entretenimiento",
    "Servicios",
    "Educación",
    "Ropa",
    "Hogar",
]

PARSE_TOOL = {
    "name": "parse_expenses",
    "description": (
        "Extrae uno o más gastos de un texto en español colombiano. "
        "Devuelve montos como enteros en COP, descripciones cortas, "
        "y mapea categoría/fuente de dinero solo si la confianza es razonable."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "Monto del gasto en COP, entero.",
                        },
                        "description": {
                            "type": "string",
                            "maxLength": 140,
                            "description": "Descripción corta y natural.",
                        },
                        "category": {
                            "type": ["string", "null"],
                            "description": (
                                "Categoría exactamente de la lista provista o null."
                            ),
                        },
                        "money_source_id": {
                            "type": ["integer", "null"],
                            "description": (
                                "ID de la fuente si el usuario la nombra explícitamente."
                            ),
                        },
                        "confidence": {
                            "type": "string",
                            "enum": ["alta", "media", "baja"],
                        },
                        "notes": {
                            "type": ["string", "null"],
                            "description": "Aclaración corta opcional.",
                        },
                    },
                    "required": [
                        "amount",
                        "description",
                        "category",
                        "money_source_id",
                        "confidence",
                    ],
                },
            }
        },
        "required": ["items"],
    },
}

class AICaptureService:

    def __init__(
        self,
        settings: Settings,
        money_source_repo: IMoneySourceRepository,
    ):
        self.settings = settings
        self.money_source_repo = money_source_repo
        if not settings.ANTHROPIC_API_KEY:
            self._client: Optional[Anthropic] = None
        else:
            self._client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def parse_text(self, text: str, user_id: int, tz: str = "America/Bogota") -> CaptureResponse:
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="text vacío")

        if self._client is None:
            raise HTTPException(
                status_code=503,
                detail="AI capture deshabilitada: ANTHROPIC_API_KEY no configurada",
            )

        sources = self._enabled_sources_for(user_id)
        system_prompt = self._build_system_prompt(sources, tz)

        try:
            message = self._client.messages.create(
                model=self.settings.CLAUDE_MODEL,
                max_tokens=self.settings.CLAUDE_MAX_TOKENS,
                system=system_prompt,
                tools=[PARSE_TOOL],
                tool_choice={"type": "tool", "name": "parse_expenses"},
                messages=[{"role": "user", "content": text}],
            )
        except APITimeoutError as exc:
            raise HTTPException(status_code=504, detail="Claude timeout") from exc
        except APIError as exc:
            raise HTTPException(
                status_code=502, detail=f"Claude error: {exc.message}"
            ) from exc

        items = self._extract_items(message)
        return CaptureResponse(
            items=items,
            transcript=text.strip(),
            model=self.settings.CLAUDE_MODEL,
        )

    def parse_attachment(
        self,
        file_bytes: bytes,
        mime_type: str,
        user_id: int,
        tz: str = "America/Bogota",
    ) -> CaptureResponse:

        if self._client is None:
            raise HTTPException(
                status_code=503,
                detail="AI capture deshabilitada: ANTHROPIC_API_KEY no configurada",
            )

        sources = self._enabled_sources_for(user_id)
        system_prompt = self._build_system_prompt(sources, tz)

        content_block = self._content_block_for_attachment(file_bytes, mime_type)
        user_text = (
            "Esta es la foto/PDF de un recibo o factura. Extrae los gastos "
            "(uno o varios items) usando la tool `parse_expenses`. Si el recibo "
            "tiene varios renglones de productos, agrúpalos sensatamente en items. "
            "Si solo hay un total, devuelve un solo item con la descripción "
            "del establecimiento."
        )

        try:
            message = self._client.messages.create(
                model=self.settings.CLAUDE_MODEL,
                max_tokens=self.settings.CLAUDE_MAX_TOKENS,
                system=system_prompt,
                tools=[PARSE_TOOL],
                tool_choice={"type": "tool", "name": "parse_expenses"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            content_block,
                            {"type": "text", "text": user_text},
                        ],
                    }
                ],
            )
        except APITimeoutError as exc:
            raise HTTPException(status_code=504, detail="Claude timeout") from exc
        except APIError as exc:
            raise HTTPException(
                status_code=502, detail=f"Claude error: {exc.message}"
            ) from exc

        items = self._extract_items(message)
        return CaptureResponse(
            items=items,
            transcript="(recibo adjunto)",
            model=self.settings.CLAUDE_MODEL,
        )

    @staticmethod
    def _content_block_for_attachment(file_bytes: bytes, mime_type: str) -> dict:
        encoded = base64.standard_b64encode(file_bytes).decode("ascii")
        if mime_type == "application/pdf":
            return {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": encoded,
                },
            }
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mime_type,
                "data": encoded,
            },
        }

    def _enabled_sources_for(self, user_id: int) -> List[dict]:
        try:
            sources = self.money_source_repo.get_by_user(user_id)
        except Exception:
            return []
        return [
            {"id": s["id"], "name": s["name"]}
            for s in sources
            if s.get("enabled")
        ]

    def _build_system_prompt(self, sources: List[dict], tz: str) -> str:
        now_local = datetime.now(pytz.timezone(tz)).strftime("%Y-%m-%d %H:%M %Z")
        cats = ", ".join(DEFAULT_CATEGORIES)
        sources_block = (
            "\n".join(f"- id={s['id']} → {s['name']}" for s in sources)
            if sources
            else "(el usuario aún no tiene fuentes registradas)"
        )

        return (
            "Eres un asistente que extrae gastos personales en pesos colombianos (COP) "
            "a partir de descripciones en español colombiano informal.\n\n"
            f"Fecha/hora actual: {now_local}.\n\n"
            "REGLAS GENERALES:\n"
            "- Devuelve siempre una llamada a la tool `parse_expenses` con la lista `items`.\n"
            "- `amount` debe ser un entero en COP (sin decimales). Convierte expresiones "
            "como 'cuarenta y cinco mil' → 45000, '5k' → 5000, '180 mil' → 180000.\n"
            "- `description` debe ser corta, natural, sin precio ni fecha.\n"
            f"- `category` debe ser EXACTAMENTE uno de: {cats}. Si no calza con confianza, usa null.\n"
            "- `confidence`: 'alta' si el monto está claro y la categoría es obvia, "
            "'media' si es razonable pero ambigua, 'baja' si tuviste que adivinar.\n"
            "- Si el texto menciona múltiples gastos (separados por 'y', comas, etc.), "
            "crea un item por cada uno.\n"
            "- Si no detectas ningún monto, devuelve items = [].\n"
            "- No inventes gastos que el usuario no mencionó.\n\n"
            "FUENTE DE DINERO (`money_source_id`) — REGLAS ESTRICTAS:\n"
            "Fuentes disponibles del usuario:\n"
            f"{sources_block}\n\n"
            "1. MATCHING FUZZY: compara la mención del usuario contra los nombres de la "
            "lista de forma case-insensitive y normalizada (sin tildes, sin acentos). "
            "Acepta matches parciales razonables:\n"
            "   - 'bancolombia', 'Bancolombia', 'banco colombia', 'cuenta de bancolombia', "
            "'con bancolombia', 'desde bancolombia', 'pague con bancolombia' → todos matchean "
            "una fuente llamada 'Bancolombia'.\n"
            "   - 'nequi', 'mi nequi', 'desde nequi', 'con la app nequi' → matchea 'Nequi'.\n"
            "   - 'efectivo', 'en efectivo', 'cash', 'plata' → matchea 'Efectivo' si existe.\n"
            "   - 'tarjeta', 'mi tarjeta', 'tdc' → matchea solo si hay UNA tarjeta en la lista.\n"
            "2. AMBIGÜEDAD: si el término del usuario es genérico ('tarjeta') y la lista tiene "
            "varias opciones que podrían matchear ('Tarjeta Visa', 'Tarjeta Master'), deja "
            "`money_source_id = null` y explica en `notes` cuáles son las opciones.\n"
            "3. SIN MENCIÓN = NULL: si el usuario NO menciona ninguna fuente, "
            "`money_source_id = null`. NO uses un valor por defecto. NO elijas la primera de "
            "la lista. NO adivines. NO inventes.\n"
            "4. MENCIÓN NO ENCONTRADA = NULL: si el usuario menciona una fuente que no está "
            "en la lista ('daviplata' cuando no existe en sus fuentes), deja "
            "`money_source_id = null` y aclara en `notes` que esa fuente no está registrada.\n\n"
            "EJEMPLOS (asumiendo fuentes: id=1 Nequi, id=2 Bancolombia, id=3 Efectivo):\n"
            "- Input: 'Compré un café de 5000 de la cuenta de bancolombia'\n"
            "  Output: [{ amount: 5000, description: 'Café', category: 'Comida', "
            "money_source_id: 2, confidence: 'alta' }]\n"
            "- Input: 'Almuerzo 15 mil'\n"
            "  Output: [{ amount: 15000, description: 'Almuerzo', category: 'Comida', "
            "money_source_id: null, confidence: 'alta' }]\n"
            "- Input: 'Pagué con nequi 30 mil de almuerzo'\n"
            "  Output: [{ amount: 30000, description: 'Almuerzo', category: 'Comida', "
            "money_source_id: 1, confidence: 'alta' }]\n"
            "- Input: 'Mercado 180 mil en efectivo y café 8 mil'\n"
            "  Output: [\n"
            "    { amount: 180000, description: 'Mercado', category: 'Mercado', "
            "money_source_id: 3, confidence: 'alta' },\n"
            "    { amount: 8000, description: 'Café', category: 'Comida', "
            "money_source_id: null, confidence: 'alta' }\n"
            "  ]\n"
            "- Input: 'Daviplata 20 mil de bus'  (si Daviplata NO está en la lista)\n"
            "  Output: [{ amount: 20000, description: 'Bus', category: 'Transporte', "
            "money_source_id: null, confidence: 'media', "
            "notes: 'Mencionaste Daviplata pero no está en tus fuentes registradas.' }]\n"
        )

    def _extract_items(self, message: Any) -> List[ParsedExpenseItem]:
        for block in getattr(message, "content", []):
            if getattr(block, "type", None) == "tool_use" and block.name == "parse_expenses":
                payload = block.input
                if isinstance(payload, str):
                    payload = json.loads(payload)
                raw_items = payload.get("items", []) if isinstance(payload, dict) else []
                return [ParsedExpenseItem(**item) for item in raw_items]
        return []
