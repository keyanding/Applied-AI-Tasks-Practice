import json
from extract_order import extract_order


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
        },
    },
    {
        "name": "missing date and email",
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
        },
    },
    {
        "name": "date normalization",
        "text": """
Bought from Paper Trail on June 5, 2026. Receipt ID PT-7781.
Paid USD 19.99 for 1 desk calendar.
Invoice email: ops@example.org
""",
        "expected": {
            "vendor": "Paper Trail",
            "order_id": "PT-7781",
            "purchase_date": "2026-06-05",
            "total_usd": 19.99,
            "invoice_email": "ops@example.org",
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
        },
    },
    {
        "name": "multiple emails",
        "text": """
Thanks for shopping at BrightDesk. Order BD-9001 was placed on 2026/06/20.
Total paid: $210.00.
For support, contact help@brightdesk.com. Please send the invoice to finance@example.com.
Items: 1 office chair, 2 monitor stands.
""",
        "expected": {
            "vendor": "BrightDesk",
            "order_id": "BD-9001",
            "purchase_date": "2026-06-20",
            "total_usd": 210.00,
            "invoice_email": "finance@example.com",
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
        },
    },
    {
        "name": "quantity missing",
        "text": """
Vendor: Cable Corner
Order: CC-2026-88
Date: 2026-06-22
Bought USB-C cable and laptop sleeve.
Total: $29.50
""",
        "expected": {
            "vendor": "Cable Corner",
            "order_id": "CC-2026-88",
            "purchase_date": "2026-06-22",
            "total_usd": 29.50,
            "invoice_email": None,
        },
    },
]


FIELDS = [
    "vendor",
    "order_id",
    "purchase_date",
    "total_usd",
    "invoice_email",
]

ITEM_CASES = [
    {
        "name": "complete order",
        "expected_items": [
            {"name": "wireless keyboard", "quantity": 2},
            {"name": "USB-C hub", "quantity": 1},
        ],
    },
    {
        "name": "missing date and email",
        "expected_items": [
            {"name": "notebook", "quantity": 3},
            {"name": "black pen", "quantity": 1},
        ],
    },
    {
        "name": "date normalization",
        "expected_items": [
            {"name": "desk calendar", "quantity": 1},
        ],
    },
    {
        "name": "no order information",
        "expected_items": [],
    },
        {
        "name": "subtotal tax shipping total",
        "expected_items": [
            {"name": "gel pen", "quantity": 2},
            {"name": "printer paper pack", "quantity": 1},
        ],
    },
    {
        "name": "multiple emails",
        "expected_items": [
            {"name": "office chair", "quantity": 1},
            {"name": "monitor stand", "quantity": 2},
        ],
    },
    {
        "name": "free gift should not be item",
        "expected_items": [
            {"name": "water bottle", "quantity": 1},
            {"name": "lunch box", "quantity": 2},
        ],
    },
    {
        "name": "quantity missing",
        "expected_items": [
            {"name": "USB-C cable", "quantity": None},
            {"name": "laptop sleeve", "quantity": None},
        ],
    },
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
    """
    Small heuristic for normalizing simple English plurals in item names.
    This is only for evaluation, not for changing the model output.
    """
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

    expected_normalized = sorted([
        {
            "name": normalize_item_name(item.get("name")),
            "quantity": item.get("quantity"),
        }
        for item in expected_items
    ], key=lambda x: x["name"])

    predicted_normalized = sorted([
        {
            "name": normalize_item_name(item.get("name")),
            "quantity": item.get("quantity"),
        }
        for item in predicted_items
    ], key=lambda x: x["name"])

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


def run_eval() -> None:
    total_fields = 0
    correct_fields = 0
    total_item_cases = 0
    correct_item_cases = 0
    failures = []

    for case in TEST_CASES:
        predicted = extract_order(case["text"])
        expected = case["expected"]
        expected_item_case = next(
            item_case for item_case in ITEM_CASES if item_case["name"] == case["name"]
        )
        expected_items = expected_item_case["expected_items"]
        predicted_items = predicted.get("items", [])

        total_item_cases += 1
        if items_match(expected_items, predicted_items):
            correct_item_cases += 1
        else:
            failures.append({
                "case": case["name"],
                "field": "items",
                "expected": expected_items,
                "predicted": predicted_items,
            })

        print("=" * 70)
        print(f"Case: {case['name']}")
        print(json.dumps(predicted, indent=2, ensure_ascii=False))

        for field in FIELDS:
            total_fields += 1
            expected_value = expected[field]
            predicted_value = predicted.get(field)

            if values_match(expected_value, predicted_value):
                correct_fields += 1
            else:
                failures.append({
                    "case": case["name"],
                    "field": field,
                    "expected": expected_value,
                    "predicted": predicted_value,
                })

    accuracy = correct_fields / total_fields
    print("\n" + "=" * 70)
    print(f"Field accuracy: {correct_fields}/{total_fields} = {accuracy:.1%}")
    item_accuracy = correct_item_cases / total_item_cases
    print(
        f"Item accuracy: {correct_item_cases}/{total_item_cases} = {item_accuracy:.1%}"
    )

    if not failures:
        print("No field failures.")
        return

    print("\nField failures:")
    for failure in failures:
        print("-" * 60)
        print(f"Case: {failure['case']}")
        print(f"Field: {failure['field']}")
        print(f"Expected: {failure['expected']}")
        print(f"Predicted: {failure['predicted']}")


if __name__ == "__main__":
    run_eval()