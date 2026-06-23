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


# -----------------------------
# 1. Extraction schema helpers
# -----------------------------

def empty_extraction() -> dict:
    return {"items": []}


def normalize_category(value) -> str:
    category = str(value or "").strip().lower()

    aliases = {
        "cab": "taxi",
        "uber": "rideshare",
        "lyft": "rideshare",
        "train": "public_transport",
        "bus": "public_transport",
        "subway": "public_transport",
        "metro": "public_transport",
        "wine": "alcohol",
        "beer": "alcohol",
        "movie": "entertainment",
        "movies": "entertainment",
        "ticket": "entertainment",
        "tickets": "entertainment",
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

    items = []

    for item in raw_items:
        if not isinstance(item, dict):
            continue

        description = str(item.get("description", "")).strip()
        category = normalize_category(item.get("category"))
        amount = coerce_float(item.get("amount"))

        if not description or amount is None:
            continue

        items.append({
            "description": description,
            "category": category,
            "amount": amount,
        })

    return {"items": items}


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


# -----------------------------
# 2. LLM extraction
# -----------------------------

def extract_expenses(user_text: str) -> dict:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    instructions = f"""
You extract explicit travel expense items from messy reimbursement text.

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
- Extract the claimed expense amount, not the reimbursable amount.
- Do not calculate reimbursement.
- Do not decide eligibility.
- If the text mentions a policy cap, do not extract the cap as the expense unless it is the amount paid.
- Use "other" if the category is unclear.
- Do not include markdown or explanation.
""".strip()

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=user_text,
    )

    return parse_json(response.output_text)


# -----------------------------
# 3. Deterministic calculator
# -----------------------------

def calculate_item(item: dict) -> dict:
    category = item["category"]
    amount = item["amount"]

    eligible = True
    reimbursable_amount = amount
    needs_receipt = amount > 25
    reason = "Eligible expense."

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
        reason = "Hotel reimbursement is capped at $180."
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
    total_reimbursable = sum(
        item["reimbursable_amount"]
        for item in calculated_items
    )

    result = {
        "items": calculated_items,
        "total_claimed": round(total_claimed, 2),
        "total_reimbursable": round(total_reimbursable, 2),
    }

    if include_debug:
        result["debug_extracted_items"] = extracted["items"]

    return result


# -----------------------------
# 4. Evaluation helpers
# -----------------------------

def money_close(a, b) -> bool:
    try:
        return abs(float(a) - float(b)) < 0.01
    except (TypeError, ValueError):
        return False


def item_key(item: dict) -> tuple:
    return (
        item.get("category"),
        round(float(item.get("claimed_amount", 0)), 2),
    )


def items_match(expected_items: list[dict], predicted_items: list[dict]) -> bool:
    if len(expected_items) != len(predicted_items):
        return False

    expected_sorted = sorted(expected_items, key=item_key)
    predicted_sorted = sorted(predicted_items, key=item_key)

    for expected, predicted in zip(expected_sorted, predicted_sorted):
        if expected["category"] != predicted.get("category"):
            return False

        if not money_close(expected["claimed_amount"], predicted.get("claimed_amount")):
            return False

        if not money_close(
            expected["reimbursable_amount"],
            predicted.get("reimbursable_amount"),
        ):
            return False

        if expected["needs_receipt"] != predicted.get("needs_receipt"):
            return False

        if expected["eligible"] != predicted.get("eligible"):
            return False

    return True


def case_passes(result: dict, expected: dict) -> bool:
    if not money_close(result.get("total_claimed"), expected["total_claimed"]):
        return False

    if not money_close(
        result.get("total_reimbursable"),
        expected["total_reimbursable"],
    ):
        return False

    if not items_match(expected["items"], result.get("items", [])):
        return False

    return True


# -----------------------------
# 5. Test cases
# -----------------------------

TEST_CASES = [
    {
        "name": "basic mixed claim",
        "text": """
During my business trip, I spent $42 on dinner, $18 on breakfast,
$40 on a taxi to the client site, and $12 on a glass of wine.
""",
        "expected": {
            "total_claimed": 112.00,
            "total_reimbursable": 93.00,
            "items": [
                {
                    "category": "dinner",
                    "claimed_amount": 42.00,
                    "reimbursable_amount": 35.00,
                    "needs_receipt": True,
                    "eligible": True,
                },
                {
                    "category": "breakfast",
                    "claimed_amount": 18.00,
                    "reimbursable_amount": 18.00,
                    "needs_receipt": False,
                    "eligible": True,
                },
                {
                    "category": "taxi",
                    "claimed_amount": 40.00,
                    "reimbursable_amount": 40.00,
                    "needs_receipt": True,
                    "eligible": True,
                },
                {
                    "category": "alcohol",
                    "claimed_amount": 12.00,
                    "reimbursable_amount": 0.00,
                    "needs_receipt": False,
                    "eligible": False,
                },
            ],
        },
    },
    {
        "name": "meal caps",
        "text": """
I had breakfast for $25, lunch for $30, and dinner for $50 while traveling for work.
""",
        "expected": {
            "total_claimed": 105.00,
            "total_reimbursable": 80.00,
            "items": [
                {
                    "category": "breakfast",
                    "claimed_amount": 25.00,
                    "reimbursable_amount": 20.00,
                    "needs_receipt": False,
                    "eligible": True,
                },
                {
                    "category": "lunch",
                    "claimed_amount": 30.00,
                    "reimbursable_amount": 25.00,
                    "needs_receipt": True,
                    "eligible": True,
                },
                {
                    "category": "dinner",
                    "claimed_amount": 50.00,
                    "reimbursable_amount": 35.00,
                    "needs_receipt": True,
                    "eligible": True,
                },
            ],
        },
    },
    {
        "name": "receipt threshold boundary",
        "text": """
I spent $25 on lunch and $25.01 on a cab ride to the airport.
""",
        "expected": {
            "total_claimed": 50.01,
            "total_reimbursable": 50.01,
            "items": [
                {
                    "category": "lunch",
                    "claimed_amount": 25.00,
                    "reimbursable_amount": 25.00,
                    "needs_receipt": False,
                    "eligible": True,
                },
                {
                    "category": "taxi",
                    "claimed_amount": 25.01,
                    "reimbursable_amount": 25.01,
                    "needs_receipt": True,
                    "eligible": True,
                },
            ],
        },
    },
    {
        "name": "do not extract cap as expense",
        "text": """
I paid $50 for dinner. I know the dinner cap is $35, but I am claiming the full $50 expense.
""",
        "expected": {
            "total_claimed": 50.00,
            "total_reimbursable": 35.00,
            "items": [
                {
                    "category": "dinner",
                    "claimed_amount": 50.00,
                    "reimbursable_amount": 35.00,
                    "needs_receipt": True,
                    "eligible": True,
                },
            ],
        },
    },
    {
        "name": "unknown and transport",
        "text": """
I bought a $900 laptop during the trip and paid $22 for subway tickets.
""",
        "expected": {
            "total_claimed": 922.00,
            "total_reimbursable": 22.00,
            "items": [
                {
                    "category": "other",
                    "claimed_amount": 900.00,
                    "reimbursable_amount": 0.00,
                    "needs_receipt": True,
                    "eligible": False,
                },
                {
                    "category": "public_transport",
                    "claimed_amount": 22.00,
                    "reimbursable_amount": 22.00,
                    "needs_receipt": False,
                    "eligible": True,
                },
            ],
        },
    },
]


# -----------------------------
# 6. Run evaluation
# -----------------------------

def run_eval() -> None:
    passed = 0
    failures = []

    for case in TEST_CASES:
        result = process_expense_claim(case["text"], include_debug=True)

        print("=" * 70)
        print(f"Case: {case['name']}")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if case_passes(result, case["expected"]):
            passed += 1
        else:
            failures.append({
                "case": case["name"],
                "expected": case["expected"],
                "result": result,
            })

    total = len(TEST_CASES)

    print("\n" + "=" * 70)
    print(f"Passed: {passed}/{total} = {passed / total:.1%}")

    if not failures:
        print("No failures.")
        return

    print("\nFailures:")
    for failure in failures:
        print("-" * 60)
        print(f"Case: {failure['case']}")
        print("Expected:")
        print(json.dumps(failure["expected"], indent=2, ensure_ascii=False))
        print("Result:")
        print(json.dumps(failure["result"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run_eval()