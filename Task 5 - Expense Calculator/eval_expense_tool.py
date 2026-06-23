import json
from expense_tool import process_expense_claim


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
        "name": "hotel cap and minibar",
        "text": """
Hotel room was $220 for one night. I also had $15 of minibar snacks.
""",
        "expected": {
            "total_claimed": 235.00,
            "total_reimbursable": 180.00,
            "items": [
                {
                    "category": "hotel",
                    "claimed_amount": 220.00,
                    "reimbursable_amount": 180.00,
                    "needs_receipt": True,
                    "eligible": True,
                },
                {
                    "category": "minibar",
                    "claimed_amount": 15.00,
                    "reimbursable_amount": 0.00,
                    "needs_receipt": False,
                    "eligible": False,
                },
            ],
        },
    },
    {
        "name": "unknown category",
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
        {
        "name": "receipt threshold boundary",
        "text": """
I spent $25 on lunch and $25.01 on a cab ride to the airport.
""",
        "expected": {
            "total_claimed": 50.01,
            "total_reimbursable": 50.00,
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
        "name": "transport aliases",
        "text": """
For the client visit, I paid $34 for Uber, $12 for the subway, and $8 for a bus.
""",
        "expected": {
            "total_claimed": 54.00,
            "total_reimbursable": 54.00,
            "items": [
                {
                    "category": "rideshare",
                    "claimed_amount": 34.00,
                    "reimbursable_amount": 34.00,
                    "needs_receipt": True,
                    "eligible": True,
                },
                {
                    "category": "public_transport",
                    "claimed_amount": 12.00,
                    "reimbursable_amount": 12.00,
                    "needs_receipt": False,
                    "eligible": True,
                },
                {
                    "category": "public_transport",
                    "claimed_amount": 8.00,
                    "reimbursable_amount": 8.00,
                    "needs_receipt": False,
                    "eligible": True,
                },
            ],
        },
    },
    {
        "name": "do not extract reimbursement amount",
        "text": """
I paid $50 for dinner. I know the cap is $35, but I am claiming the full $50 expense.
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
        "name": "entertainment and meal mixed",
        "text": """
I spent $28 on lunch with the client and $45 on movie tickets after the meeting.
""",
        "expected": {
            "total_claimed": 73.00,
            "total_reimbursable": 25.00,
            "items": [
                {
                    "category": "lunch",
                    "claimed_amount": 28.00,
                    "reimbursable_amount": 25.00,
                    "needs_receipt": True,
                    "eligible": True,
                },
                {
                    "category": "entertainment",
                    "claimed_amount": 45.00,
                    "reimbursable_amount": 0.00,
                    "needs_receipt": True,
                    "eligible": False,
                },
            ],
        },
    },
]


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


def run_eval() -> None:
    passed = 0
    failures = []

    for case in TEST_CASES:
        result = process_expense_claim(case["text"])

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