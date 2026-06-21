from collections import Counter
from classify import classify_request


CASES = [
    {
        "name": "refund plus slow app",
        "text": "Can I get a refund? Also, the app is very slow.",
        "expected": "pricing_question",
    },
    {
        "name": "billing page crashes",
        "text": "The billing page crashes when I try to update my card.",
        "expected": "bug_report",
    },
    {
        "name": "paid but cannot access",
        "text": "I can't access the Pro features even though I paid.",
        "expected": "account_access",
    },
    {
        "name": "data exposure",
        "text": "The model exposed another user's private email address in its answer.",
        "expected": "safety_concern",
    },
    {
        "name": "password wrong on web but mobile works",
        "text": "The login page says my password is wrong, but I can sign in on mobile.",
        "expected": "account_access",
    },
    {
        "name": "feature request for speed",
        "text": "Could you make the dashboard faster? It takes 20 seconds to load.",
        "expected": "feature_request",
    },
]


def run_repeat_eval(num_runs: int = 10) -> None:
    for case in CASES:
        outputs = []

        for _ in range(num_runs):
            predicted = classify_request(case["text"])
            outputs.append(predicted)

        counts = Counter(outputs)

        print("=" * 70)
        print(f"Case: {case['name']}")
        print(f"Text: {case['text']}")
        print(f"Expected: {case['expected']}")
        print(f"Outputs: {dict(counts)}")

        if len(counts) == 1 and case["expected"] in counts:
            print("Status: stable pass")
        elif case["expected"] in counts:
            print("Status: flaky")
        else:
            print("Status: stable fail")


if __name__ == "__main__":
    run_repeat_eval(num_runs=10)