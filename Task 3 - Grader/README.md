# Task 3: LLM-as-Judge Rubric Grader

This task implements a small language-model-based answer grading tool.

Given a user question and a candidate answer, the tool scores the answer on:

* `accuracy`
* `completeness`
* `clarity`
* `safety`
* `overall`

Each score is an integer from 1 to 5. The tool also returns short feedback.

The model is `gpt-5-nano` through the OpenAI API.

## Run the grader

From the project root:

```bash
python task3_grader/grade_answer.py
```

## Run evaluation

Run the fixed evaluation set:

```bash
python task3_grader/eval_grader.py
```

Run repeated stability checks:

```bash
python task3_grader/repeat_eval_grader.py
```

Run the assessment scratch template:

```bash
python task3_grader/exam_scratch_template_grader.py
```

## Design Notes

The grader uses a rubric prompt and asks the model to return JSON with five scores and a feedback string.

The implementation includes:

1. JSON parsing,
2. score normalization,
3. range-based evaluation,
4. overall consistency checks,
5. repeated stability checks.

Because grading is subjective, the evaluator does not require exact score matches. Instead, each test case defines acceptable score ranges for the dimensions that matter.

For example:

* a factually wrong answer should have low `accuracy` and low `overall`;
* unsafe medical or legal advice should have low `safety`;
* an answer that violates “exactly two reasons” should be penalized for `completeness`, not `safety`;
* a cautious legal answer can be safe and accurate even if it is not fully complete.

The consistency check catches obviously incoherent grades, such as a very high `overall` score when `accuracy` or `safety` is very low.

## Files

* `grade_answer.py`: grader implementation
* `eval_grader.py`: fixed range-based evaluation set
* `repeat_eval_grader.py`: repeated stability checks
* `exam_scratch_template_grader.py`: one-file assessment template
* `analysis_report_task3.md`: short write-up of approach, findings, and limitations
