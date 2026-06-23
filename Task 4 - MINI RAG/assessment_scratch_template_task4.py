# Task 4: Mini RAG Evidence-Grounded QA

This task implements a small evidence-grounded question-answering tool over a travel reimbursement policy.

Given a user question, the system:

1. retrieves relevant policy chunks,
2. asks `gpt-5-nano` to answer using only those chunks,
3. returns structured JSON with an answer, citations, and an evidence-sufficiency flag.

The output schema is:

```json
{
  "answer": "string",
  "cited_chunk_ids": ["P1"],
  "enough_evidence": true
}
```

## Run the QA tool

From the project root:

```bash
python task4_mini_rag/rag_qa.py
```

## Run evaluation

Run the fixed evaluation set:

```bash
python task4_mini_rag/eval_rag_qa.py
```

Run repeated stability checks:

```bash
python task4_mini_rag/repeat_eval_rag_qa.py
```

## Design Notes

The system uses a small in-memory policy corpus. Each chunk has a stable id such as `P1`, `P2`, or `P3`.

The retriever is a simple keyword-based retriever with a few high-precision boosts for important policy concepts, such as:

* receipt requirements,
* transportation expenses,
* dollar thresholds.

The generator is instructed to:

* use only retrieved policy chunks,
* answer only the question asked,
* avoid adjacent but unnecessary policy facts,
* cite every directly supporting chunk,
* set `enough_evidence` to `false` when the provided chunks are insufficient.

The implementation also includes a citation guardrail: final citations can only include chunk ids that were actually retrieved and shown to the model.

## Evaluation Strategy

The evaluator checks:

* whether `enough_evidence` is correct,
* whether the answer cites the correct direct-support chunks,
* whether the answer contains key facts,
* whether unsupported answers avoid citations.

The evaluation includes hard cases such as:

* questions requiring multiple chunks,
* insufficient-evidence questions,
* reimbursement limits,
* receipt requirements,
* over-citation risks.

Repeated evaluation is used to detect cases where the model sometimes over-answers or cites unnecessary chunks.

## Files

* `rag_qa.py`: mini RAG implementation
* `eval_rag_qa.py`: fixed evaluation set
* `repeat_eval_rag_qa.py`: repeated stability checks
* `analysis_report_task4.md`: short write-up of approach, findings, and limitations
