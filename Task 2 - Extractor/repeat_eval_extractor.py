from collections import Counter
import json

from extract_order import extract_order
from eval_extractor import (
    TEST_CASES,
    ITEM_CASES,
    FIELDS,
    values_match,
    items_match,
    normalize_item_name,
)


REPEAT_CASE_NAMES = [
    "subtotal tax shipping total",
    "multiple emails",
    "free gift should not be item",
    "quantity missing",
]


def canonical_for_comparison(order: dict) -> str:
    """
    Canonicalize outputs for stability comparison.

    This is stricter than pass/fail scoring in structure, but tolerant to
    harmless surface differences such as item-name casing.
    """
    normalized = dict(order)

    normalized_items = []
    for item in order.get("items", []):
        normalized_items.append({
            "name": normalize_item_name(item.get("name")),
            "quantity": item.get("quantity"),
        })

    normalized["items"] = sorted(
        normalized_items,
        key=lambda item: item["name"],
    )

    return json.dumps(normalized, sort_keys=True, ensure_ascii=False)

def get_expected_items(case_name: str) -> list[dict]:
    for item_case in ITEM_CASES:
        if item_case["name"] == case_name:
            return item_case["expected_items"]
    return []


def check_prediction(case: dict, predicted: dict) -> bool:
    expected = case["expected"]

    for field in FIELDS:
        if not values_match(expected[field], predicted.get(field)):
            return False

    expected_items = get_expected_items(case["name"])
    predicted_items = predicted.get("items", [])

    if not items_match(expected_items, predicted_items):
        return False

    return True


def run_repeat_eval(num_runs: int = 5) -> None:
    selected_cases = [
        case for case in TEST_CASES if case["name"] in REPEAT_CASE_NAMES
    ]

    for case in selected_cases:
        outcomes = []
        raw_outputs = []

        for _ in range(num_runs):
            predicted = extract_order(case["text"])
            raw_outputs.append(canonical_for_comparison(predicted))

            passed = check_prediction(case, predicted)
            outcomes.append("pass" if passed else "fail")

        counts = Counter(outcomes)
        unique_outputs = len(set(raw_outputs))

        print("=" * 70)
        print(f"Case: {case['name']}")
        print(f"Pass/fail counts: {dict(counts)}")
        print(f"Unique normalized outputs: {unique_outputs}")
        if unique_outputs > 1:
            print("Unique outputs:")
            for output in sorted(set(raw_outputs)):
                print(output)

        if counts.get("fail", 0) == 0:
            print("Status: stable pass")
        elif counts.get("pass", 0) > 0:
            print("Status: flaky")
        else:
            print("Status: stable fail")


if __name__ == "__main__":
    run_repeat_eval(num_runs=5)