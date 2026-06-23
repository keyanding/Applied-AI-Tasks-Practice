from collections import Counter
import json

from rag_qa import answer_question, retrieve
from eval_rag_qa import TEST_CASES, case_passes


REPEAT_CASE_NAMES = [
    "taxi receipt requirement",
    "dinner reimbursement",
    "laptop not covered",
    "hotel above limit without approval",
    "alcohol with dinner",
]


def compact_result(result: dict) -> str:
    """
    Compact representation for comparing repeated RAG outputs.
    We care about evidence status and citations more than exact wording.
    """
    compact = {
        "enough_evidence": result.get("enough_evidence"),
        "cited_chunk_ids": sorted(result.get("cited_chunk_ids", [])),
    }

    return json.dumps(compact, sort_keys=True)


def run_repeat_eval(num_runs: int = 5) -> None:
    selected_cases = [
        case for case in TEST_CASES if case["name"] in REPEAT_CASE_NAMES
    ]

    for case in selected_cases:
        outcomes = []
        compact_outputs = []

        retrieved_chunks = retrieve(case["question"], top_k=3)
        retrieved_ids = [chunk["id"] for chunk in retrieved_chunks]

        for _ in range(num_runs):
            result = answer_question(case["question"])

            passed = case_passes(result, case["expected"])
            outcomes.append("pass" if passed else "fail")
            compact_outputs.append(compact_result(result))

        outcome_counts = Counter(outcomes)
        unique_outputs = sorted(set(compact_outputs))

        print("=" * 70)
        print(f"Case: {case['name']}")
        print(f"Question: {case['question']}")
        print(f"Retrieved chunk ids: {retrieved_ids}")
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