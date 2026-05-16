
from __future__ import annotations

import calendar
import json
from datetime import datetime
from typing import Any, Dict, List

import pytz
from anthropic import Anthropic, APIError, APITimeoutError
from fastapi import HTTPException

from app.config.settings import Settings
from app.repositories.interfaces.budget_repository import IBudgetRepository
from app.repositories.interfaces.expense_repository import IExpenseRepository
from app.repositories.interfaces.money_source_repository import IMoneySourceRepository
from app.schemas.chat import ChatMessage
from app.utils.dates import get_period_range, local_day_end_utc, local_day_start_utc

MAX_ITER = 5

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "get_summary",
        "description": (
            "Devuelve el total gastado y el desglose por categoría del usuario "
            "para un período. Úsala para preguntas del tipo 'cuánto llevo este "
            "mes', 'en qué estoy gastando más', 'cuánto gasté hoy'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly"],
                    "description": "daily=hoy, weekly=semana actual, monthly=mes en curso.",
                }
            },
            "required": ["period"],
        },
    },
    {
        "name": "query_expenses",
        "description": (
            "Lista detallada de gastos del usuario con filtros opcionales. "
            "Úsala cuando necesites ejemplos concretos para sustentar una "
            "sugerencia (ej. 'qué cafés compró este mes')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly"],
                },
                "category": {
                    "type": ["string", "null"],
                    "description": "Filtra por categoría exacta (case-insensitive). null para no filtrar.",
                },
                "money_source_id": {
                    "type": ["integer", "null"],
                    "description": "Filtra por fuente de dinero. null para no filtrar.",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 30,
                },
            },
            "required": ["period"],
        },
    },
    {
        "name": "get_budgets_status",
        "description": (
            "Presupuestos activos del usuario con cuánto ha gastado vs el "
            "límite del período correspondiente. Úsala para 'cuánto me queda "
            "del presupuesto', 'voy bien con el presupuesto'."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_money_sources",
        "description": (
            "Lista de fuentes de dinero (cuentas, billeteras, efectivo) con "
            "sus balances actuales y si están habilitadas. Úsala para 'cuánto "
            "tengo en X', 'cuál es mi saldo'."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "compare_months",
        "description": (
            "Compara totales y desglose por categoría entre dos meses. Útil "
            "para 'cómo me fue este mes vs el pasado'. Formato YYYY-MM."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "month_a": {
                    "type": "string",
                    "description": "Primer mes en formato YYYY-MM.",
                    "pattern": r"^\d{4}-\d{2}$",
                },
                "month_b": {
                    "type": "string",
                    "description": "Segundo mes en formato YYYY-MM.",
                    "pattern": r"^\d{4}-\d{2}$",
                },
            },
            "required": ["month_a", "month_b"],
        },
    },
]

def _month_range_utc(month: str, tz: str) -> tuple[str, str]:
    year, mo = month.split("-")
    year_i, mo_i = int(year), int(mo)
    last_day = calendar.monthrange(year_i, mo_i)[1]
    start = local_day_start_utc(f"{year_i:04d}-{mo_i:02d}-01", tz).isoformat()
    end = local_day_end_utc(f"{year_i:04d}-{mo_i:02d}-{last_day:02d}", tz).isoformat()
    return start, end

class AIChatService:

    def __init__(
        self,
        settings: Settings,
        expense_repo: IExpenseRepository,
        budget_repo: IBudgetRepository,
        money_source_repo: IMoneySourceRepository,
    ):
        self.settings = settings
        self.expense_repo = expense_repo
        self.budget_repo = budget_repo
        self.money_source_repo = money_source_repo
        if not settings.ANTHROPIC_API_KEY:
            self._client: Anthropic | None = None
        else:
            self._client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def chat(
        self,
        history: List[ChatMessage],
        user_id: int,
        tz: str = "America/Bogota",
    ) -> tuple[ChatMessage, int]:

        if self._client is None:
            raise HTTPException(
                status_code=503,
                detail="Chat IA deshabilitado: ANTHROPIC_API_KEY no configurada",
            )

        system_prompt = self._build_system_prompt(tz)
        messages = [{"role": m.role, "content": m.content} for m in history]

        for iteration in range(1, MAX_ITER + 1):
            try:
                resp = self._client.messages.create(
                    model=self.settings.CLAUDE_MODEL,
                    max_tokens=self.settings.CLAUDE_MAX_TOKENS,
                    system=system_prompt,
                    tools=TOOLS,
                    messages=messages,
                )
            except APITimeoutError as exc:
                raise HTTPException(status_code=504, detail="Claude timeout") from exc
            except APIError as exc:
                raise HTTPException(
                    status_code=502, detail=f"Claude error: {exc.message}"
                ) from exc

            if resp.stop_reason != "tool_use":
                text = self._extract_text(resp)
                return (
                    ChatMessage(role="assistant", content=text or "(sin respuesta)"),
                    iteration,
                )

            assistant_blocks = [block.model_dump() for block in resp.content]
            messages.append({"role": "assistant", "content": assistant_blocks})

            tool_results = []
            for block in resp.content:
                if getattr(block, "type", None) != "tool_use":
                    continue
                result = self._dispatch_tool(block.name, block.input or {}, user_id, tz)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str, ensure_ascii=False),
                    }
                )
            messages.append({"role": "user", "content": tool_results})

        return (
            ChatMessage(
                role="assistant",
                content=(
                    "No pude llegar a una respuesta concluyente — intenté usar "
                    "varias herramientas y me quedé sin vueltas. ¿Podrías "
                    "reformular la pregunta más específica?"
                ),
            ),
            MAX_ITER,
        )

    def _dispatch_tool(
        self, name: str, args: Dict[str, Any], user_id: int, tz: str
    ) -> Dict[str, Any]:
        try:
            if name == "get_summary":
                return self._tool_get_summary(user_id, args.get("period", "monthly"), tz)
            if name == "query_expenses":
                return self._tool_query_expenses(user_id, args, tz)
            if name == "get_budgets_status":
                return self._tool_get_budgets_status(user_id, tz)
            if name == "get_money_sources":
                return self._tool_get_money_sources(user_id)
            if name == "compare_months":
                return self._tool_compare_months(
                    user_id, args["month_a"], args["month_b"], tz
                )
        except Exception as exc:  # noqa: BLE001
            return {"error": f"{name} falló: {exc}"}
        return {"error": f"Tool desconocida: {name}"}

    def _tool_get_summary(self, user_id: int, period: str, tz: str) -> Dict[str, Any]:
        start, end = get_period_range(period, None, None, tz)
        s = start.isoformat() if start else None
        e = end.isoformat() if end else None
        summary = self.expense_repo.get_summary(user_id, s, e)
        return {"period": period, **summary}

    def _tool_query_expenses(
        self, user_id: int, args: Dict[str, Any], tz: str
    ) -> Dict[str, Any]:
        period = args.get("period", "monthly")
        start, end = get_period_range(period, None, None, tz)
        s = start.isoformat() if start else None
        e = end.isoformat() if end else None

        rows = self.expense_repo.get_filtered(user_id, s, e)

        category = args.get("category")
        money_source_id = args.get("money_source_id")
        limit = min(args.get("limit", 30) or 30, 50)

        if category:
            cat_lower = category.lower().strip()
            rows = [
                r for r in rows
                if r.get("category") and r["category"].lower().strip() == cat_lower
            ]
        if money_source_id is not None:
            rows = [r for r in rows if r.get("money_source_id") == money_source_id]

        items = [
            {
                "id": r["id"],
                "amount": r["amount"],
                "description": r["description"],
                "category": r.get("category"),
                "date": r["date"],
                "money_source": r.get("ms_name"),
            }
            for r in rows[:limit]
        ]
        return {
            "period": period,
            "filters": {
                "category": category,
                "money_source_id": money_source_id,
                "limit": limit,
            },
            "count": len(items),
            "items": items,
        }

    def _tool_get_budgets_status(self, user_id: int, tz: str) -> Dict[str, Any]:
        budgets = self.budget_repo.get_enabled_by_user(user_id)
        out = []
        for b in budgets:
            start, end = get_period_range(b["type"], None, None, tz)
            if start is None or end is None:
                continue
            spent = self.expense_repo.get_spent_in_period(
                user_id, start.isoformat(), end.isoformat()
            )
            limit = float(b["amount"])
            percentage = round((spent / limit) * 100) if limit > 0 else 0
            out.append(
                {
                    "type": b["type"],
                    "limit": limit,
                    "spent": spent,
                    "remaining": limit - spent,
                    "percentage": percentage,
                }
            )
        return {"budgets": out}

    def _tool_get_money_sources(self, user_id: int) -> Dict[str, Any]:
        sources = self.money_source_repo.get_by_user(user_id)
        return {
            "sources": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "balance": s["balance"],
                    "enabled": bool(s["enabled"]),
                }
                for s in sources
            ]
        }

    def _tool_compare_months(
        self, user_id: int, month_a: str, month_b: str, tz: str
    ) -> Dict[str, Any]:
        start_a, end_a = _month_range_utc(month_a, tz)
        start_b, end_b = _month_range_utc(month_b, tz)
        summary_a = self.expense_repo.get_summary(user_id, start_a, end_a)
        summary_b = self.expense_repo.get_summary(user_id, start_b, end_b)

        cats_a = {c["category"]: c["total"] for c in summary_a.get("by_category", [])}
        cats_b = {c["category"]: c["total"] for c in summary_b.get("by_category", [])}
        all_cats = sorted(set(cats_a) | set(cats_b))
        by_category_diff = [
            {
                "category": c,
                "month_a": cats_a.get(c, 0.0),
                "month_b": cats_b.get(c, 0.0),
                "delta": cats_b.get(c, 0.0) - cats_a.get(c, 0.0),
            }
            for c in all_cats
        ]
        return {
            "month_a": {"month": month_a, **summary_a},
            "month_b": {"month": month_b, **summary_b},
            "total_delta": summary_b["total"] - summary_a["total"],
            "by_category_diff": by_category_diff,
        }

    def _build_system_prompt(self, tz: str) -> str:
        now_local = datetime.now(pytz.timezone(tz)).strftime("%Y-%m-%d %H:%M %Z")
        return (
            "Eres el asistente financiero personal de un usuario colombiano. "
            "Solo respondes sobre la vida financiera del usuario en esta app. "
            f"Hoy es {now_local}. Moneda: pesos colombianos (COP).\n\n"
            "REGLAS:\n"
            "- Antes de afirmar un número, llama a la tool correspondiente. NO inventes datos.\n"
            "- Sé conciso, en español colombiano, con tono cercano pero profesional.\n"
            "- Formatea montos con separadores de miles y prefijo $, ej: '$45.000', '$1.200.000'.\n"
            "- Usa markdown ligero: bullets cortos, **negrita** para destacar, sin headings grandes.\n"
            "- Si la pregunta no tiene que ver con la vida financiera del usuario, "
            "redirige amablemente en una frase.\n"
            "- Para sugerencias de ahorro: identifica la categoría con mayor gasto vía "
            "get_summary, mira ejemplos concretos vía query_expenses, y propón 2-3 "
            "recortes específicos. No digas 'ahorra más' — di 'el rubro Comida "
            "tiene N cafés de $X, podrías reducir a M por semana'.\n"
            "- No des asesoría legal, fiscal ni de inversiones. Solo análisis de gastos personales.\n\n"
            "TOOLS DISPONIBLES:\n"
            "- get_summary(period): total + desglose por categoría.\n"
            "- query_expenses(period, category?, money_source_id?, limit?): lista detallada.\n"
            "- get_budgets_status(): presupuestos activos con gasto vs límite.\n"
            "- get_money_sources(): cuentas/billeteras con balances.\n"
            "- compare_months(month_a, month_b): comparación entre dos meses (formato YYYY-MM).\n\n"
            "Llama varias tools si hace falta. No hagas suposiciones cuando puedas consultar."
        )

    @staticmethod
    def _extract_text(resp: Any) -> str:
        parts: List[str] = []
        for block in getattr(resp, "content", []):
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "\n".join(parts).strip()
