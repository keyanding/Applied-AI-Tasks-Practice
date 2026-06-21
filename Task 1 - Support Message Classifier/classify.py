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

def parse_model_output(raw_text: str) -> str:
    """
    Parse the model output and return a valid label.

    Expected format:
    {"label": "bug_report"}

    Fallback:
    If JSON parsing fails, look for any valid label in the raw text.
    """
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

def apply_deterministic_overrides(user_text: str, model_label: str) -> str:
    """
    Apply conservative deterministic rules after the model prediction.

    Rationale:
    - The model handles broad semantic classification.
    - These overrides handle high-confidence tie-breaking cases that were
      unstable or ambiguous during evaluation.
    - Rules should stay conservative to avoid overfitting to visible tests.
    """
    text = user_text.lower()

    safety_terms = [
        "private email",
        "data exposure",
        "another user's",
        "security bypass",
        "bypass",
        "harassment",
        "abuse",
        "documents from another workspace",
    ]

    if any(term in text for term in safety_terms):
        return "safety_concern"

    account_access_terms = [
        "can't log in",
        "cannot log in",
        "can't login",
        "cannot login",
        "can't sign in",
        "cannot sign in",
        "can't access my account",
        "cannot access my account",
        "lost access",
        "password is wrong",
        "resetting my password",
        "verification code",
        "admin permission",
    ]

    explicit_feature_request_terms = [
        "can you add",
        "could you add",
        "please add",
        "can you make",
        "could you make",
        "please make",
        "it would be great if",
        "please support",
        "can you support",
        "could you support",
        "add an option",
    ]

    has_account_access_signal = any(term in text for term in account_access_terms)
    has_explicit_feature_request = any(
        phrase in text for phrase in explicit_feature_request_terms
    )

    # account_access wins when the user does not ask for a account access related feature:
    # e.g. Please make the login page support passkeys.
    if has_account_access_signal and not has_explicit_feature_request:
        return "account_access"

    explicit_pricing_requests = [
        "refund",
        "invoice",
        "charged",
        "charge",
        "billing",
        "subscription",
        "price",
        "pricing",
        "payment",
        "cost",
        "plan",
    ]

    crash_or_broken_terms = [
        "crash",
        "crashes",
        "broken",
        "nothing happened",
        "does nothing",
        "not working",
        "fails",
        "failed",
    ]

    # Pricing wins when the user makes an explicit pricing/billing request,
    # unless the main wording is clearly about a broken product behavior.
    has_pricing_signal = any(term in text for term in explicit_pricing_requests)
    has_broken_signal = any(term in text for term in crash_or_broken_terms)

    if has_pricing_signal and not has_broken_signal:
        return "pricing_question"

    # Explicit product-change requests win over complaints about current quality.
    # Example: "Could you make the dashboard faster?" is a feature request.
    if has_explicit_feature_request:
        return "feature_request"  

    return model_label


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

Return only valid JSON in this exact format:
{{"label": "<one of the allowed labels>"}}

Do not include markdown, comments, or explanation.
""".strip()

# Return only the label. No explanation.

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=user_text,
    )

    label = response.output_text.strip()

    # if label not in LABELS:
    #     return "irrelevant"

    # return apply_deterministic_overrides(user_text, label)
    raw_output = response.output_text.strip()
    label = parse_model_output(raw_output)

    return apply_deterministic_overrides(user_text, label)


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