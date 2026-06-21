import os
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


def classify_request(user_text: str) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    instructions = f"""
You are a precise classifier for user support messages.

Classify the user's message into exactly one of these labels:
{", ".join(LABELS)}

Label meanings:
- bug_report: something is broken, crashing, failing, unusually slow, or not working as expected
- feature_request: the user asks for a new capability, integration, improvement, or product change
- pricing_question: the user asks about price, billing, subscription, refund, invoice, plan limits, charges, or payment
- account_access: the user has login, password, account, verification, permission, or access problems
- safety_concern: the user reports harmful, unsafe, abusive, privacy, security, data exposure, or policy-sensitive behavior
- irrelevant: the message is unrelated, spam, unclear, or not a support request

Tie-breaking rules:
1. If the message involves data exposure, security bypass, abuse, harassment, or unsafe use, choose safety_concern.
2. If the user explicitly asks for refund, invoice, subscription, billing, price, payment, or charges, choose pricing_question unless the main issue is a security/privacy concern.
3. If the user cannot log in, cannot access their account, lacks permission, or is blocked from using paid features, choose account_access.
4. If the user describes an existing product behavior that is broken, crashing, failing, or unexpectedly slow, choose bug_report.
5. If the user asks to add, improve, support, or change a product capability, choose feature_request.
6. If none of the labels clearly apply, choose irrelevant.

Return only the label. No explanation.
""".strip()

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=user_text,
    )

    label = response.output_text.strip()

    if label not in LABELS:
        return "irrelevant"

    return label


if __name__ == "__main__":
    examples = [
        "The app crashes every time I upload a PDF.",
        "Can you add Slack integration?",
        "How much does the Pro plan cost?",
        "I can't log into my account after resetting my password.",
        "The chatbot gave instructions for bypassing a security system.",
        "asdf qwer hello banana",
    ]

    for text in examples:
        print(f"Input: {text}")
        print(f"Label: {classify_request(text)}")
        print()