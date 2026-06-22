import os
import json
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI


load_dotenv(find_dotenv())

MODEL = "gpt-5-nano"


EXPECTED_KEYS = [
    "vendor",
    "order_id",
    "purchase_date",
    "total_usd",
    "items",
    "invoice_email",
]


def empty_order() -> dict:
    return {
        "vendor": None,
        "order_id": None,
        "purchase_date": None,
        "total_usd": None,
        "items": [],
        "invoice_email": None,
    }


def coerce_optional_string(value):
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    return text


def coerce_optional_float(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def coerce_optional_int(value):
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_order(data: dict) -> dict:
    """
    Enforce a stable output schema regardless of model formatting.
    Extra fields are dropped. Missing or invalid fields become null/defaults.
    """
    if not isinstance(data, dict):
        return empty_order()

    result = empty_order()

    result["vendor"] = coerce_optional_string(data.get("vendor"))
    result["order_id"] = coerce_optional_string(data.get("order_id"))
    result["purchase_date"] = coerce_optional_string(data.get("purchase_date"))
    result["total_usd"] = coerce_optional_float(data.get("total_usd"))
    result["invoice_email"] = coerce_optional_string(data.get("invoice_email"))

    raw_items = data.get("items", [])
    if isinstance(raw_items, list):
        normalized_items = []

        for item in raw_items:
            if not isinstance(item, dict):
                continue

            name = coerce_optional_string(item.get("name"))
            quantity = coerce_optional_int(item.get("quantity"))

            if name is None:
                continue

            normalized_items.append({
                "name": name,
                "quantity": quantity,
            })

        result["items"] = normalized_items

    return result


def parse_json(raw_text: str) -> dict:
    raw_text = raw_text.strip()

    try:
        return normalize_order(json.loads(raw_text))
    except json.JSONDecodeError:
        pass

    # Simple fallback for cases where the model wraps JSON in markdown fences.
    if raw_text.startswith("```"):
        cleaned = raw_text.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).strip()
        try:
            return normalize_order(json.loads(cleaned))
        except json.JSONDecodeError:
            pass

    return empty_order()


def extract_order(text: str) -> dict:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    instructions = """
You extract structured order information from messy text.

Return only valid JSON with exactly these fields:
{
  "vendor": string or null,
  "order_id": string or null,
  "purchase_date": "YYYY-MM-DD" or null,
  "total_usd": number or null,
  "items": [
    {
      "name": string,
      "quantity": integer or null
    }
  ],
  "invoice_email": string or null
}

Rules:
- Use null when a field is missing.
- Normalize dates to YYYY-MM-DD when possible.
- Normalize money amounts to a number in USD.
- Do not infer details that are not present.
- Do not include markdown or explanation.
- For items, include only products that were purchased or explicitly bought.
- Exclude free gifts, promotional items, samples, shipping, tax, discounts, notes, and contact information from items.
- If an item is mentioned without a quantity, use null for quantity.
""".strip()

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=text,
    )

    return parse_json(response.output_text)


if __name__ == "__main__":
    sample_text = """
Hi, I bought 2 wireless keyboards and 1 USB-C hub from Acme Store on 2026-06-18.
The order number is AC-99127. Total was $148.50 including tax.
Please send the invoice to keyan@example.com.
"""

    result = extract_order(sample_text)
    print(json.dumps(result, indent=2, ensure_ascii=False))