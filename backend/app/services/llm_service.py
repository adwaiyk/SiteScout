"""
LLM Service (Groq) — SiteScout Milestone 4
AI-powered investment narratives and Q&A using Groq's free-tier LLMs.
Gracefully degrades if Groq is unavailable.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_groq_client = None
_groq_available = False


def _get_groq_client():
    """Lazily initialize the Groq client."""
    global _groq_client, _groq_available
    if _groq_client is not None:
        return _groq_client

    try:
        from groq import Groq
        from app.config import get_settings
        settings = get_settings()
        api_key = getattr(settings, "GROQ_API_KEY", "")
        if not api_key:
            logger.warning("GROQ_API_KEY not set — AI features disabled.")
            _groq_available = False
            return None

        _groq_client = Groq(api_key=api_key)
        _groq_available = True
        logger.info("Groq client initialized successfully.")
        return _groq_client
    except ImportError:
        logger.warning("groq package not installed — AI features disabled.")
        _groq_available = False
        return None
    except Exception as e:
        logger.warning("Failed to initialize Groq client: %s", e)
        _groq_available = False
        return None


def _get_model_name() -> str:
    """Get the configured Groq model name."""
    try:
        from app.config import get_settings
        return getattr(get_settings(), "GROQ_MODEL", "llama-3.3-70b-versatile")
    except Exception:
        return "llama-3.3-70b-versatile"


def generate_investment_narrative(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a concise, plain-English investment feasibility summary.
    3-5 sentences, grounded strictly in the computed numbers.
    """
    client = _get_groq_client()
    if client is None:
        return {
            "narrative": None,
            "available": False,
            "error": "AI summary unavailable — Groq API not configured.",
        }

    # Build a structured prompt with the actual analysis data
    prompt = _build_narrative_prompt(analysis_data)

    try:
        response = client.chat.completions.create(
            model=_get_model_name(),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a renewable energy investment analyst. Generate a concise, "
                        "professional feasibility summary for a non-technical stakeholder. "
                        "Use ONLY the numbers provided in the analysis data. Do NOT fabricate "
                        "any figures. Write 3-5 sentences. Be specific about financial metrics, "
                        "energy yield, and site suitability. If the site is not feasible, "
                        "clearly state why."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=400,
            timeout=15.0,
        )

        narrative = response.choices[0].message.content.strip()
        return {
            "narrative": narrative,
            "available": True,
            "model": _get_model_name(),
            "error": None,
        }

    except Exception as e:
        logger.error("Groq narrative generation failed: %s", e)
        return {
            "narrative": None,
            "available": False,
            "error": f"AI summary unavailable — {type(e).__name__}",
        }


def answer_site_question(
    question: str,
    analysis_data: Dict[str, Any],
    shap_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Answer a natural-language question about a specific site's analysis.
    Grounded in the actual analysis JSON + SHAP explainability output.
    """
    client = _get_groq_client()
    if client is None:
        return {
            "answer": None,
            "available": False,
            "error": "AI Q&A unavailable — Groq API not configured.",
        }

    context = _build_qa_context(analysis_data, shap_data)

    try:
        response = client.chat.completions.create(
            model=_get_model_name(),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a renewable energy site assessment expert. Answer the user's "
                        "question about a specific site using ONLY the provided analysis data. "
                        "Do NOT invent facts not present in the data. Reference specific numbers "
                        "from the analysis. If the data doesn't contain information to answer "
                        "the question, say so clearly. Keep your answer concise (2-4 sentences)."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Site Analysis Data:\n{context}\n\nQuestion: {question}",
                },
            ],
            temperature=0.2,
            max_tokens=300,
            timeout=15.0,
        )

        answer = response.choices[0].message.content.strip()
        return {
            "answer": answer,
            "available": True,
            "model": _get_model_name(),
            "error": None,
        }

    except Exception as e:
        logger.error("Groq Q&A failed: %s", e)
        return {
            "answer": None,
            "available": False,
            "error": f"AI Q&A unavailable — {type(e).__name__}",
        }


def _build_narrative_prompt(data: Dict[str, Any]) -> str:
    """Build a structured prompt from the analysis data."""
    parts = ["Generate an investment feasibility narrative based on this site analysis:\n"]

    # Location
    coords = data.get("coordinates", {})
    parts.append(f"Location: {coords.get('latitude', 'N/A')}°N, {coords.get('longitude', 'N/A')}°E")

    # Suitability
    suit = data.get("suitability", {})
    parts.append(f"Suitability Score: {suit.get('overall_score', 'N/A')}/100 ({suit.get('classification', 'N/A')})")

    # Feasibility
    feas = data.get("feasibility", {})
    parts.append(f"Technically Feasible: {'Yes' if feas.get('is_feasible') else 'No'}")
    failures = feas.get("hard_constraint_summary", {}).get("failure_reasons", [])
    if failures:
        parts.append(f"Constraint Failures: {', '.join(failures)}")

    # Energy
    energy = data.get("energy_yield", {})
    parts.append(f"Annual Energy Yield: {energy.get('annual_energy_yield_mwh', 0):,.0f} MWh")
    parts.append(f"Deployment Type: {energy.get('energy_type', 'N/A')}")

    # Financial
    fin = data.get("financial", {})
    parts.append(f"Project Cost (CAPEX): ${fin.get('estimated_project_cost_usd', 0):,.0f}")
    parts.append(f"Annual Revenue: ${fin.get('annual_revenue_usd', 0):,.0f}")
    parts.append(f"Payback Period: {fin.get('payback_period_years', 'N/A')} years")
    parts.append(f"NPV: ${fin.get('npv_usd', 0):,.0f}")
    parts.append(f"LCOE: ${fin.get('lcoe_usd_per_mwh', 0):.2f}/MWh")
    parts.append(f"IRR: {fin.get('irr_pct', 0):.1f}%")

    # Micrositing
    ms = data.get("micrositing", {})
    dp = ms.get("deployment_plan", {})
    parts.append(f"Recommended Technology: {dp.get('recommended_technology', 'N/A')}")
    parts.append(f"Total Capacity: {dp.get('recommended_capacity_mw', 0):.1f} MW")
    parts.append(f"Expansion: {dp.get('expansion_status', 'N/A')}")

    return "\n".join(parts)


def _build_qa_context(data: Dict[str, Any], shap_data: Optional[Dict[str, Any]] = None) -> str:
    """Build context string for Q&A from analysis data."""
    import json

    # Slim down the data to avoid token limits — exclude yearly cash flows
    slim_data = {}
    for key, value in data.items():
        if key == "financial" and isinstance(value, dict):
            slim_fin = {k: v for k, v in value.items() if k != "yearly_cash_flows"}
            slim_data[key] = slim_fin
        else:
            slim_data[key] = value

    context = json.dumps(slim_data, indent=2, default=str)

    if shap_data:
        context += "\n\nSHAP Explainability Data:\n"
        shap_slim = {
            "model_type": shap_data.get("model_type"),
            "predicted_value": shap_data.get("predicted_value"),
            "top_positive_drivers": shap_data.get("top_positive_drivers"),
            "top_negative_drivers": shap_data.get("top_negative_drivers"),
        }
        context += json.dumps(shap_slim, indent=2, default=str)

    # Truncate if too long (Groq has context limits)
    if len(context) > 6000:
        context = context[:6000] + "\n... (truncated)"

    return context
