import os
import json
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

MODEL = "gpt-5-nano"

LABELS = [
    "bug_report",
    "feature_request",
    "pricing_question",
    "account_access",
    "safety_concern",
    "irrelevant",
]


def call_model(input_text: str) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    instructions = f"""
You are a precise classifier.

Choose exactly one label:
{", ".join(LABELS)}

Return only JSON:
{{"label": "<one label>"}}
""".strip()

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=input_text,
    )

    return response.output_text


def parse_output(raw_text: str) -> str:
    raw_text = raw_text.strip()

    try:
        data = json.loads(raw_text)
        label = data.get("label", "").strip()
        if label in LABELS:
            return label
    except json.JSONDecodeError:
        pass

    for label in LABELS:
        if label in raw_text:
            return label

    return "irrelevant"


def predict(input_text: str) -> str:
    raw_output = call_model(input_text)
    label = parse_output(raw_output)
    return label


def run_eval(test_cases: list[dict]) -> None:
    correct = 0
    failures = []

    for i, case in enumerate(test_cases, start=1):
        predicted = predict(case["text"])
        expected = case["expected"]

        if predicted == expected:
            correct += 1
        else:
            failures.append({
                "case_id": i,
                "text": case["text"],
                "expected": expected,
                "predicted": predicted,
            })

    total = len(test_cases)
    print(f"Accuracy: {correct}/{total} = {correct / total:.1%}")

    if failures:
        print("\nFailures:")
        for failure in failures:
            print("-" * 60)
            print(f"Case: {failure['case_id']}")
            print(f"Text: {failure['text']}")
            print(f"Expected: {failure['expected']}")
            print(f"Predicted: {failure['predicted']}")
    else:
        print("No failures.")


if __name__ == "__main__":
    test_cases = [
        {
            "text": "The app crashes when I upload a PDF.",
            "expected": "bug_report",
        },
        {
            "text": "Can you add Slack integration?",
            "expected": "feature_request",
        },
        {
            "text": "How much does the Pro plan cost?",
            "expected": "pricing_question",
        },
        {
            "text": "I can't log into my account.",
            "expected": "account_access",
        },
        {
            "text": "The model exposed another user's private email.",
            "expected": "safety_concern",
        },
        {
            "text": "asdf banana hello",
            "expected": "irrelevant",
        },
    ]

    run_eval(test_cases)