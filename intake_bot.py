"""
Guided buying chatbot — powered by Google Gemini (google-genai SDK).
"""
# Use Windows certificate store (Accenture corporate SSL interception)
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_client = None


def _resolve_api_key() -> str:
    """Look up the Gemini key from Streamlit secrets first (cloud deploy),
    then fall back to environment variables (local .env)."""
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY", "")


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        key = _resolve_api_key()
        if not key or key.startswith("AIzaSy..."):
            raise ValueError("GEMINI_API_KEY not configured. Set it in Streamlit secrets or .env file.")
        _client = genai.Client(api_key=key)
    return _client


SYSTEM_PROMPT = """You are Centrica's intelligent Guided Buying Assistant — a friendly, professional AI that helps Centrica employees procure goods and services efficiently.

Your job is to conduct a SHORT, natural conversation to capture everything needed to raise a purchase request. Ask ONE question at a time. Keep responses concise and professional.

You must collect (in any conversational order):
1. What they need (item/service description — enough detail to write an RFQ)
2. Quantity and unit (e.g. "50 laptops", "1 annual contract", "3 days consultancy")
3. Maximum budget (£ GBP — if they don't know, suggest they check with their finance partner)
4. Business unit / department (British Gas Services / Centrica Energy Storage / Connected Home / Centrica plc)
5. Delivery / start date required

Rules:
- Be warm but efficient. Don't ask more than 5 questions total.
- Validate budget figures — gently challenge if they seem very high or very low for the category.
- Classify risk tier automatically: LOW (routine goods/services < £50k), MEDIUM (services > £50k or any IT involving data), HIGH (>£200k or involves critical infrastructure / third-party data processing).
- Once you have all 5 fields, respond with a summary prefixed exactly with "INTAKE_COMPLETE:" followed by valid JSON on the next line. The JSON must have these keys: buyer_name, buyer_department, business_unit, category, subcategory, description, quantity, unit, max_budget, required_by, priority ("standard" or "urgent"), risk_tier ("low"/"medium"/"high").
- If risk_tier is "high", add a note: "This request will be escalated to your Category Manager for review due to high value / complexity."
- Category should be one of: IT Equipment & Software, Facilities Management, Professional Services, Fleet & Transport, Engineering & Maintenance, Office Supplies & Furniture, Health & Safety Equipment, Marketing & Communications, Other.
- Never mention competitors, never give financial advice, never commit Centrica to any terms."""


def _build_gemini_contents(messages: list) -> list:
    """Convert OpenAI-style [{role, content}] to Gemini contents format."""
    contents = []
    for m in messages:
        role = "model" if m["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))
    return contents


def chat_stream(messages: list, buyer_name: str = ""):
    """Stream a response from the intake bot. Yields text chunks."""
    client = _get_client()
    model = os.getenv("GEMINI_MODEL_PRIMARY", "gemini-2.0-flash")

    system = SYSTEM_PROMPT
    if buyer_name:
        system += f"\n\nThe user's name is {buyer_name}. Use their first name occasionally."

    contents = _build_gemini_contents(messages) if messages else [
        types.Content(role="user", parts=[types.Part(text="Hello, start the intake.")])
    ]

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.4,
            max_output_tokens=500,
        ),
    ):
        if chunk.text:
            yield chunk.text


def extract_intake_json(full_response: str) -> dict | None:
    """Extract and parse the JSON after INTAKE_COMPLETE: marker."""
    if "INTAKE_COMPLETE:" not in full_response:
        return None
    try:
        after = full_response.split("INTAKE_COMPLETE:", 1)[1].strip()
        start = after.index("{")
        depth, end = 0, start
        for i, ch in enumerate(after[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        return json.loads(after[start:end])
    except Exception:
        return None


def classify_category(description: str) -> str:
    """Quick Gemini call to classify a free-text description into a procurement category."""
    client = _get_client()
    model = os.getenv("GEMINI_MODEL_FAST", "gemini-2.0-flash")
    resp = client.models.generate_content(
        model=model,
        contents=(
            "Classify this procurement request into exactly one of these categories: "
            "IT Equipment & Software, Facilities Management, Professional Services, "
            "Fleet & Transport, Engineering & Maintenance, Office Supplies & Furniture, "
            "Health & Safety Equipment, Marketing & Communications, Other.\n\n"
            f"Request: {description}\n\nRespond with only the category name."
        ),
        config=types.GenerateContentConfig(temperature=0, max_output_tokens=20),
    )
    return resp.text.strip()
