from collections import Counter
import json

from expense_tool import process_expense_claim
from eval_expense_tool import TEST_CASES, case_passes


REPEAT_CASE_NAMES = [
    "receipt threshold boundary",
    "transport aliases",
    "do not extract reimbursement amount",
    "entertainment and meal mixed",
]


def compact_result(result: dict) -> str:
    """
    Compact representation for comparing repeated outputs.
    We compare the final calculated structure, not exact reason wording.
    """
    compact_items = []

    for item in result.get("items", []):
        compact_items.append({
            "category": item.get("category"),
            "claimed_amount": item.get("claimed_amount"),
            "reimbursable_amount": item.get("reimbursable_amount"),
            "needs_receipt": item.get("needs_receipt"),
            "eligible": item.get("eligible"),
        })

    compact_items = sorted(
        compact_items,
        key=lambda item: (
            item["category"],
            item["claimed_amount"],
            item["reimbursable_amount"],
        ),
    )

    compact = {
        "items": compact_items,
        "total_claimed": result.get("total_claimed"),
        "total_reimbursable": result.get("total_reimbursable"),
    }

    return json.dumps(compact, sort_keys=True)


def run_repeat_eval(num_runs: int = 5) -> None:
    selected_cases = [
        case for case in TEST_CASES if case["name"] in REPEAT_CASE_NAMES
    ]

    for case in selected_cases:
        outcomes = []
        compact_outputs = []

        for _ in range(num_runs):
            result = process_expense_claim(case["text"])

            passed = case_passes(result, case["expected"])
            outcomes.append("pass" if passed else "fail")
            compact_outputs.append(compact_result(result))

        outcome_counts = Counter(outcomes)
        unique_outputs = sorted(set(compact_outputs))

        print("=" * 70)
        print(f"Case: {case['name']}")
        print(f"Pass/fail counts: {dict(outcome_counts)}")
        print(f"Unique compact outputs: {len(unique_outputs)}")

        if len(unique_outputs) > 1:
            print("Output variants:")
            for output in unique_outputs:
                print(output)

        if outcome_counts.get("fail", 0) == 0:
            print("Status: stable pass")
        elif outcome_counts.get("pass", 0) > 0:
            print("Status: flaky")
        else:
            print("Status: stable fail")


if __name__ == "__main__":
    run_repeat_eval(num_runs=5)