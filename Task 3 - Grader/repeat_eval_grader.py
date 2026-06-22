from collections import Counter
import json

from grade_answer import grade_answer
from eval_grader import TEST_CASES, case_passes, overall_is_consistent


REPEAT_CASE_NAMES = [
    "fluent but violates instruction",
    "clear but factually wrong",
    "overconfident legal advice",
    "good cautious legal answer",
]


def compact_grade(grade: dict) -> str:
    """
    Compact representation for comparing repeated judge outputs.
    We care mostly about scores, not exact feedback wording.
    """
    score_only = {
        "accuracy": grade.get("accuracy"),
        "completeness": grade.get("completeness"),
        "clarity": grade.get("clarity"),
        "safety": grade.get("safety"),
        "overall": grade.get("overall"),
    }

    return json.dumps(score_only, sort_keys=True)


def run_repeat_eval(num_runs: int = 5) -> None:
    selected_cases = [
        case for case in TEST_CASES if case["name"] in REPEAT_CASE_NAMES
    ]

    for case in selected_cases:
        outcomes = []
        score_outputs = []
        consistency_outputs = []

        for _ in range(num_runs):
            grade = grade_answer(case["question"], case["answer"])

            passed = case_passes(grade, case["expected"])
            consistent = overall_is_consistent(grade)

            outcomes.append("pass" if passed else "fail")
            consistency_outputs.append("consistent" if consistent else "inconsistent")
            score_outputs.append(compact_grade(grade))

        outcome_counts = Counter(outcomes)
        consistency_counts = Counter(consistency_outputs)
        unique_score_outputs = sorted(set(score_outputs))

        print("=" * 70)
        print(f"Case: {case['name']}")
        print(f"Pass/fail counts: {dict(outcome_counts)}")
        print(f"Consistency counts: {dict(consistency_counts)}")
        print(f"Unique score outputs: {len(unique_score_outputs)}")

        if len(unique_score_outputs) > 1:
            print("Score variants:")
            for output in unique_score_outputs:
                print(output)

        if outcome_counts.get("fail", 0) == 0:
            print("Status: stable pass")
        elif outcome_counts.get("pass", 0) > 0:
            print("Status: flaky")
        else:
            print("Status: stable fail")


if __name__ == "__main__":
    run_repeat_eval(num_runs=5)