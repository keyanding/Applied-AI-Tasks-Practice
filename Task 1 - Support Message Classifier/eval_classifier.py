from classify import classify_request


TEST_CASES = [
    # Straightforward cases
    {
        "text": "The app crashes every time I upload a PDF.",
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
        "text": "I can't log into my account after resetting my password.",
        "expected": "account_access",
    },
    {
        "text": "The chatbot gave instructions for bypassing a security system.",
        "expected": "safety_concern",
    },
    {
        "text": "asdf qwer hello banana",
        "expected": "irrelevant",
    },

    # More realistic / hidden-test-like cases
    {
        "text": "I was charged twice this month. Can someone check my invoice?",
        "expected": "pricing_question",
    },
    {
        "text": "The export button does nothing when I click it.",
        "expected": "bug_report",
    },
    {
        "text": "It would be great if this supported Notion databases.",
        "expected": "feature_request",
    },
    {
        "text": "I lost access after changing my phone number.",
        "expected": "account_access",
    },
    {
        "text": "A user is using the tool to generate harassment messages.",
        "expected": "safety_concern",
    },
    {
        "text": "Do you like pizza?",
        "expected": "irrelevant",
    },

    # Ambiguous cases
    {
        "text": "I can't access the Pro features even though I paid.",
        "expected": "account_access",
    },
    {
        "text": "The billing page crashes when I try to update my card.",
        "expected": "bug_report",
    },
    {
        "text": "Can I get a refund? Also, the app is very slow.",
        "expected": "pricing_question",
    },
    {
        "text": "Please make the login page support passkeys.",
        "expected": "feature_request",
    },
    
        # Hard / adversarial cases
    {
        "text": "I don't want a refund, I just want to know why my invoice changed.",
        "expected": "pricing_question",
    },
    {
        "text": "The login page says my password is wrong, but I can sign in on mobile.",
        "expected": "account_access",
    },
    {
        "text": "The model exposed another user's private email address in its answer.",
        "expected": "safety_concern",
    },
    {
        "text": "Could you make the dashboard faster? It takes 20 seconds to load.",
        "expected": "feature_request",
    },
    {
        "text": "The dashboard now takes 20 seconds to load after yesterday's update.",
        "expected": "bug_report",
    },
    {
        "text": "Your product is too expensive and also crashes constantly.",
        "expected": "bug_report",
    },
    {
        "text": "Can I use this for free if I am a student?",
        "expected": "pricing_question",
    },
    {
        "text": "I need admin permission to invite my teammate.",
        "expected": "account_access",
    },
    {
        "text": "Please add an option to delete all my data permanently.",
        "expected": "feature_request",
    },
    {
        "text": "I found a way to see documents from another workspace.",
        "expected": "safety_concern",
    },
    {
        "text": "The button should be blue instead of green.",
        "expected": "feature_request",
    },
    {
        "text": "I clicked the blue button and nothing happened.",
        "expected": "bug_report",
    },
]


def run_eval() -> None:
    correct = 0
    failures = []

    for i, case in enumerate(TEST_CASES, start=1):
        predicted = classify_request(case["text"])
        expected = case["expected"]

        if predicted == expected:
            correct += 1
        else:
            failures.append(
                {
                    "case_id": i,
                    "text": case["text"],
                    "expected": expected,
                    "predicted": predicted,
                }
            )

    total = len(TEST_CASES)
    accuracy = correct / total

    print(f"Accuracy: {correct}/{total} = {accuracy:.1%}")
    print()

    if not failures:
        print("No failures.")
        return

    print("Failures:")
    for failure in failures:
        print("-" * 60)
        print(f"Case: {failure['case_id']}")
        print(f"Text: {failure['text']}")
        print(f"Expected: {failure['expected']}")
        print(f"Predicted: {failure['predicted']}")


if __name__ == "__main__":
    run_eval()