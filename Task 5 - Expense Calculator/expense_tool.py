import os
import json
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI


load_dotenv(find_dotenv())

MODEL = "gpt-5-nano"

VALID_CATEGORIES = [
    "breakfast",
    "lunch",
    "dinner",
    "hotel",
    "taxi",
    "rideshare",
    "public_transport",
    "alcohol",
    "minibar",
    "entertainment",
    "other",
]


def empty_extraction() -> dict:
    return {
        "items": [],
    }


def normalize_category(value: str) -> str:
    category = str(value or "").strip().lower()

    aliases = {
        "cab": "taxi",
        "uber": "rideshare",
        "lyft": "rideshare",
        "train": "public_transport",
        "bus": "public_transport",
        "subway": "public_transport",
        "wine": "alcohol",
        "beer": "alcohol",
        "movie": "entertainment",
        "movies": "entertainment",
    }

    category = aliases.get(category, category)

    if category not in VALID_CATEGORIES:
        return "other"

    return category


def coerce_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_extraction(data: dict) -> dict:
    if not isinstance(data, dict):
        return empty_extraction()

    raw_items = data.get("items", [])
    if not isinstance(raw_items, list):
        return empty_extraction()

    normalized_items = []

    for item in raw_items:
        if not isinstance(item, dict):
            continue

        description = str(item.get("description", "")).strip()
        category = normalize_category(item.get("category"))
        amount = coerce_float(item.get("amount"))

        if not description or amount is None:
            continue

        normalized_items.append({
            "description": description,
            "category": category,
            "amount": amount,
        })

    return {
        "items": normalized_items,
    }


def parse_json(raw_text: str) -> dict:
    raw_text = raw_text.strip()

    try:
        return normalize_extraction(json.loads(raw_text))
    except json.JSONDecodeError:
        pass

    if raw_text.startswith("```"):
        cleaned = raw_text.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).strip()

        try:
            return normalize_extraction(json.loads(cleaned))
        except json.JSONDecodeError:
            pass

    return empty_extraction()


def extract_expenses(user_text: str) -> dict:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    instructions = f"""
You extract expense items from messy travel reimbursement text.

Allowed categories:
{", ".join(VALID_CATEGORIES)}

Return only valid JSON in this exact format:
{{
  "items": [
    {{
      "description": string,
      "category": one of the allowed categories,
      "amount": number
    }}
  ]
}}

Rules:
- Extract only explicit expenses with dollar amounts.
- Do not calculate reimbursement.
- Do not decide eligibility.
- Use "other" if the category is unclear.
- Do not include markdown or explanation.
""".strip()

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=user_text,
    )

    return parse_json(response.output_text)


def calculate_item(item: dict) -> dict:
    category = item["category"]
    amount = item["amount"]

    eligible = True
    reimbursable_amount = amount
    reason = "Eligible expense."
    needs_receipt = amount > 25

    if category == "breakfast":
        reimbursable_amount = min(amount, 20)
        reason = "Breakfast is capped at $20."
    elif category == "lunch":
        reimbursable_amount = min(amount, 25)
        reason = "Lunch is capped at $25."
    elif category == "dinner":
        reimbursable_amount = min(amount, 35)
        reason = "Dinner is capped at $35."
    elif category == "hotel":
        reimbursable_amount = min(amount, 180)
        reason = "Hotel reimbursement is capped at $180 per night."
    elif category in ["taxi", "rideshare", "public_transport"]:
        reimbursable_amount = amount
        reason = "Business-related transportation is reimbursable."
    elif category in ["alcohol", "minibar", "entertainment"]:
        eligible = False
        reimbursable_amount = 0
        reason = "This category is not reimbursable."
    else:
        eligible = False
        reimbursable_amount = 0
        reason = "The policy does not provide enough information for this category."

    return {
        "description": item["description"],
        "category": category,
        "claimed_amount": round(amount, 2),
        "reimbursable_amount": round(reimbursable_amount, 2),
        "needs_receipt": needs_receipt,
        "eligible": eligible,
        "reason": reason,
    }


def process_expense_claim(user_text: str, include_debug: bool = False) -> dict:
    extracted = extract_expenses(user_text)

    calculated_items = [
        calculate_item(item)
        for item in extracted["items"]
    ]

    total_claimed = sum(item["claimed_amount"] for item in calculated_items)
    total_reimbursable = sum(item["reimbursable_amount"] for item in calculated_items)

    result = {
        "items": calculated_items,
        "total_claimed": round(total_claimed, 2),
        "total_reimbursable": round(total_reimbursable, 2),
    }

    if include_debug:
        result["debug_extracted_items"] = extracted["items"]

    return result


if __name__ == "__main__":
    sample = """
During my business trip, I spent $42 on dinner, $18 on breakfast,
$40 on a taxi to the client site, and $12 on a glass of wine.
"""

    result = process_expense_claim(sample, include_debug=True)
    print(json.dumps(result, indent=2, ensure_ascii=False))