from rag_qa import answer_question, retrieve


TEST_CASES = [
    {
        "name": "dinner reimbursement",
        "question": "Can I expense dinner during a business trip?",
        "expected": {
            "enough_evidence": True,
            "required_citations": ["P2"],
            "answer_keywords": ["dinner", "$35"],
        },
    },
    {
        "name": "business class approval",
        "question": "Can I book a business-class flight?",
        "expected": {
            "enough_evidence": True,
            "required_citations": ["P1"],
            "answer_keywords": ["director approval"],
        },
    },
    {
        "name": "minibar not reimbursable",
        "question": "Are minibar charges reimbursable?",
        "expected": {
            "enough_evidence": True,
            "required_citations": ["P6"],
            "answer_keywords": ["not reimbursable"],
        },
    },
    {
        "name": "hotel nightly limit",
        "question": "What is the hotel reimbursement limit per night?",
        "expected": {
            "enough_evidence": True,
            "required_citations": ["P3"],
            "answer_keywords": ["$180"],
        },
    },
    {
        "name": "expense report deadline",
        "question": "How soon do I need to submit my expense report after a trip?",
        "expected": {
            "enough_evidence": True,
            "required_citations": ["P5"],
            "answer_keywords": ["30 days"],
        },
    },
        {
        "name": "laptop not covered",
        "question": "Can I expense a new laptop?",
        "expected": {
            "enough_evidence": False,
            "required_citations": [],
            "answer_any_keywords": [
                "not contain enough information",
                "do not specify",
                "does not specify",
                "do not provide enough information",
                "not enough information",
            ],
        },
    },
        {
        "name": "lunch reimbursement cap",
        "question": "If I spend $30 on lunch during approved business travel, can I get the full amount reimbursed?",
        "expected": {
            "enough_evidence": True,
            "required_citations": ["P2"],
            "answer_keywords": ["$25"],
        },
    },
    {
        "name": "taxi receipt requirement",
        "question": "I took a $40 taxi during a business trip. Is it reimbursable, and do I need a receipt?",
        "expected": {
            "enough_evidence": True,
            "required_citations": ["P4", "P5"],
            "answer_keywords": ["reimbursable", "receipt"],
        },
    },
    {
        "name": "hotel above limit without approval",
        "question": "Can I expense a $220 hotel room if I did not get Finance approval before the trip?",
        "expected": {
            "enough_evidence": True,
            "required_citations": ["P3"],
            "answer_keywords": ["$180", "Finance"],
        },
    },
    {
        "name": "alcohol with dinner",
        "question": "Can I expense a glass of wine with dinner during business travel?",
        "expected": {
            "enough_evidence": True,
            "required_citations": ["P2"],
            "answer_keywords": ["alcohol", "not reimbursable"],
        },
    },
]


def normalize_text(text: str) -> str:
    return str(text).lower().strip()


# def citations_match(expected_ids: list[str], predicted_ids: list[str]) -> bool:
#     return set(expected_ids).issubset(set(predicted_ids))
def citations_match(expected_ids: list[str], predicted_ids: list[str]) -> bool:
    expected_set = set(expected_ids)
    predicted_set = set(predicted_ids)

    # For insufficient-evidence answers, we expect no citations.
    if not expected_set:
        return not predicted_set

    # For supported answers, require exactly the expected direct-support citations.
    return predicted_set == expected_set


def answer_contains_keywords(answer: str, keywords: list[str]) -> bool:
    normalized_answer = normalize_text(answer)

    for keyword in keywords:
        if normalize_text(keyword) not in normalized_answer:
            return False

    return True


def case_passes(result: dict, expected: dict) -> bool:
    if result.get("enough_evidence") != expected["enough_evidence"]:
        return False

    predicted_citations = result.get("cited_chunk_ids", [])
    if not citations_match(expected["required_citations"], predicted_citations):
        return False

    if "answer_keywords" in expected:
        if not answer_contains_keywords(result.get("answer", ""), expected["answer_keywords"]):
            return False

    if "answer_any_keywords" in expected:
        normalized_answer = normalize_text(result.get("answer", ""))
        has_any_keyword = any(
            normalize_text(keyword) in normalized_answer
            for keyword in expected["answer_any_keywords"]
        )
        if not has_any_keyword:
            return False

    return True


def run_eval() -> None:
    passed = 0
    failures = []

    for case in TEST_CASES:
        result = answer_question(case["question"])
        expected = case["expected"]

        print("=" * 70)
        print(f"Case: {case['name']}")
        print(f"Question: {case['question']}")

        retrieved_chunks = retrieve(case["question"], top_k=3)
        retrieved_ids = [chunk["id"] for chunk in retrieved_chunks]
        print(f"Retrieved chunk ids: {retrieved_ids}")

        for chunk in retrieved_chunks:
            print(f"[{chunk['id']}] {chunk['text']}")

        print(f"Result: {result}")

        if case_passes(result, expected):
            passed += 1
        else:
            failures.append({
                "case": case["name"],
                "question": case["question"],
                "expected": expected,
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
        print(f"Question: {failure['question']}")
        print(f"Expected: {failure['expected']}")
        print(f"Result: {failure['result']}")


if __name__ == "__main__":
    run_eval()