import os
import json
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI


load_dotenv(find_dotenv())

MODEL = "gpt-5-nano"


# -----------------------------
# 1. Schema helpers
# -----------------------------

def empty_result() -> dict:
    return {
        "vendor": None,
        "order_id": None,
        "purchase_date": None,
        "total_usd": None,
        "items": [],
        "invoice_email": None,
    }


def to_optional_string(value):
    if value is None:
        return None

    text = str(value).strip()
    return text if text else None


def to_optional_float(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_optional_int(value):
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_result(data: dict) -> dict:
    """
    Ensure the output always has the expected schema.
    Drop extra fields and coerce simple types.
    """
    if not isinstance(data, dict):
        return empty_result()

    result = empty_result()

    result["vendor"] = to_optional_string(data.get("vendor"))
    result["order_id"] = to_optional_string(data.get("order_id"))
    result["purchase_date"] = to_optional_string(data.get("purchase_date"))
    result["total_usd"] = to_optional_float(data.get("total_usd"))
    result["invoice_email"] = to_optional_string(data.get("invoice_email"))

    raw_items = data.get("items", [])
    if isinstance(raw_items, list):
        items = []

        for item in raw_items:
            if not isinstance(item, dict):
                continue

            name = to_optional_string(item.get("name"))
            quantity = to_optional_int(item.get("quantity"))

            if name is None:
                continue

            items.append({
                "name": name,
                "quantity": quantity,
            })

        result["items"] = items

    return result


# -----------------------------
# 2. Model call + parser
# -----------------------------

def call_model(input_text: str) -> str:
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
- For items, include only products that were purchased or explicitly bought.
- Exclude free gifts, promotional items, samples, shipping, tax, discounts, notes, and contact information from items.
- If an item is mentioned without a quantity, use null for quantity.
- Do not include markdown or explanation.
""".strip()

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=input_text,
    )

    return response.output_text


def parse_json(raw_text: str) -> dict:
    raw_text = raw_text.strip()

    try:
        return normalize_result(json.loads(raw_text))
    except json.JSONDecodeError:
        pass

    # Fallback if model wraps JSON in markdown fences.
    if raw_text.startswith("```"):
        cleaned = raw_text.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).strip()

        try:
            return normalize_result(json.loads(cleaned))
        except json.JSONDecodeError:
            pass

    return empty_result()


def extract_order(input_text: str) -> dict:
    raw_output = call_model(input_text)
    return parse_json(raw_output)


# -----------------------------
# 3. Evaluation helpers
# -----------------------------

FIELDS = [
    "vendor",
    "order_id",
    "purchase_date",
    "total_usd",
    "invoice_email",
]


def normalize_string(value):
    if value is None:
        return None

    return str(value).strip().lower()


def values_match(expected, predicted) -> bool:
    if expected is None:
        return predicted is None

    if isinstance(expected, float):
        try:
            return abs(float(predicted) - expected) < 0.01
        except (TypeError, ValueError):
            return False

    return normalize_string(expected) == normalize_string(predicted)


def singularize_word(word: str) -> str:
    if word.endswith("ies"):
        return word[:-3] + "y"

    if word.endswith(("ches", "shes", "xes", "zes", "ses")):
        return word[:-2]

    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]

    return word


def normalize_item_name(name):
    if name is None:
        return ""

    normalized = str(name).strip().lower()
    normalized = normalized.replace("-", " ")
    normalized = " ".join(normalized.split())

    words = normalized.split()
    words = [singularize_word(word) for word in words]

    return " ".join(words)


def items_match(expected_items, predicted_items) -> bool:
    if not isinstance(predicted_items, list):
        return False

    expected_normalized = sorted(
        [
            {
                "name": normalize_item_name(item.get("name")),
                "quantity": item.get("quantity"),
            }
            for item in expected_items
        ],
        key=lambda item: item["name"],
    )

    predicted_normalized = sorted(
        [
            {
                "name": normalize_item_name(item.get("name")),
                "quantity": item.get("quantity"),
            }
            for item in predicted_items
        ],
        key=lambda item: item["name"],
    )

    if len(expected_normalized) != len(predicted_normalized):
        return False

    for expected, predicted in zip(expected_normalized, predicted_normalized):
        if expected["name"] != predicted["name"]:
            return False

        try:
            if int(expected["quantity"]) != int(predicted["quantity"]):
                return False
        except (TypeError, ValueError):
            if expected["quantity"] != predicted["quantity"]:
                return False

    return True


# -----------------------------
# 4. Test cases
# -----------------------------

TEST_CASES = [
    {
        "name": "complete order",
        "text": """
Hi, I bought 2 wireless keyboards and 1 USB-C hub from Acme Store on 2026-06-18.
The order number is AC-99127. Total was $148.50 including tax.
Please send the invoice to keyan@example.com.
""",
        "expected": {
            "vendor": "Acme Store",
            "order_id": "AC-99127",
            "purchase_date": "2026-06-18",
            "total_usd": 148.50,
            "invoice_email": "keyan@example.com",
            "items": [
                {"name": "wireless keyboard", "quantity": 2},
                {"name": "USB-C hub", "quantity": 1},
            ],
        },
    },
    {
        "name": "missing fields",
        "text": """
Order #ZX-1008 from Northwind Supplies. Total: $32.10.
Items: 3 notebooks, 1 black pen.
""",
        "expected": {
            "vendor": "Northwind Supplies",
            "order_id": "ZX-1008",
            "purchase_date": None,
            "total_usd": 32.10,
            "invoice_email": None,
            "items": [
                {"name": "notebook", "quantity": 3},
                {"name": "black pen", "quantity": 1},
            ],
        },
    },
    {
        "name": "subtotal tax shipping total",
        "text": """
Receipt from Metro Office Mart
Order ID: MOM-4432
Date: 06/21/2026
Items:
- 2 gel pens
- 1 printer paper pack

Subtotal: $18.00
Shipping: $4.99
Tax: $1.72
Grand total: $24.71
Billing contact: billing-team@example.com
""",
        "expected": {
            "vendor": "Metro Office Mart",
            "order_id": "MOM-4432",
            "purchase_date": "2026-06-21",
            "total_usd": 24.71,
            "invoice_email": "billing-team@example.com",
            "items": [
                {"name": "gel pen", "quantity": 2},
                {"name": "printer paper pack", "quantity": 1},
            ],
        },
    },
    {
        "name": "free gift should not be item",
        "text": """
Order #GG-777 from GreenGoods on July 1, 2026.
Purchased: 1 water bottle, 2 lunch boxes.
Free gift included: sticker pack.
Amount paid: $42.00.
Invoice email: receipts@example.net
""",
        "expected": {
            "vendor": "GreenGoods",
            "order_id": "GG-777",
            "purchase_date": "2026-07-01",
            "total_usd": 42.00,
            "invoice_email": "receipts@example.net",
            "items": [
                {"name": "water bottle", "quantity": 1},
                {"name": "lunch box", "quantity": 2},
            ],
        },
    },
    {
        "name": "no order information",
        "text": """
Hi, can you tell me your opening hours this weekend?
""",
        "expected": {
            "vendor": None,
            "order_id": None,
            "purchase_date": None,
            "total_usd": None,
            "invoice_email": None,
            "items": [],
        },
    },
]


# -----------------------------
# 5. Run evaluation
# -----------------------------

def run_eval() -> None:
    total_fields = 0
    correct_fields = 0
    total_item_cases = 0
    correct_item_cases = 0
    failures = []

    for case in TEST_CASES:
        predicted = extract_order(case["text"])
        expected = case["expected"]

        print("=" * 70)
        print(f"Case: {case['name']}")
        print(json.dumps(predicted, indent=2, ensure_ascii=False))

        for field in FIELDS:
            total_fields += 1

            if values_match(expected[field], predicted.get(field)):
                correct_fields += 1
            else:
                failures.append({
                    "case": case["name"],
                    "field": field,
                    "expected": expected[field],
                    "predicted": predicted.get(field),
                })

        total_item_cases += 1

        if items_match(expected["items"], predicted.get("items", [])):
            correct_item_cases += 1
        else:
            failures.append({
                "case": case["name"],
                "field": "items",
                "expected": expected["items"],
                "predicted": predicted.get("items", []),
            })

    field_accuracy = correct_fields / total_fields
    item_accuracy = correct_item_cases / total_item_cases

    print("\n" + "=" * 70)
    print(f"Field accuracy: {correct_fields}/{total_fields} = {field_accuracy:.1%}")
    print(f"Item accuracy: {correct_item_cases}/{total_item_cases} = {item_accuracy:.1%}")

    if not failures:
        print("No failures.")
        return

    print("\nFailures:")
    for failure in failures:
        print("-" * 60)
        print(f"Case: {failure['case']}")
        print(f"Field: {failure['field']}")
        print(f"Expected: {failure['expected']}")
        print(f"Predicted: {failure['predicted']}")


if __name__ == "__main__":
    run_eval()