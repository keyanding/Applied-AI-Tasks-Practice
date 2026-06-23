# Task 4 Report: Mini RAG Evidence-Grounded QA

## Problem

I built a small evidence-grounded question-answering tool for a company travel reimbursement policy. Given a user question, the system retrieves relevant policy chunks and uses `gpt-5-nano` to answer using only those chunks.

The output is structured JSON with:

* `answer`
* `cited_chunk_ids`
* `enough_evidence`

The system should answer only when the retrieved policy chunks contain enough evidence. If the evidence is insufficient, it should say so and avoid unsupported claims.

## Approach

I started with a small in-memory policy corpus. Each policy chunk has an id such as `P1`, `P2`, and so on. I implemented a simple keyword-based retriever that selects the top relevant chunks for a question.

The model receives only the retrieved chunks and is instructed to:

* answer using only the provided chunks,
* cite every chunk that directly supports the answer,
* avoid citing related but unnecessary chunks,
* set `enough_evidence` to `false` when the chunks do not provide enough information,
* avoid using outside knowledge.

The model output is parsed as JSON and normalized into a stable schema. I also added a citation guardrail so that the final citations can only include chunks that were actually retrieved and shown to the model.

## Evaluation

I evaluated the system on questions that test three key properties:

1. answer correctness,
2. citation correctness,
3. insufficient-evidence handling.

The evaluator checks:

* whether `enough_evidence` is correct,
* whether the required supporting chunk ids are cited,
* whether the answer contains key facts,
* whether unsupported answers avoid citations.

I also added hard cases that require multiple chunks, such as a taxi reimbursement question where the answer needs both the transportation policy and the receipt policy.

## Findings and Iterations

The most important failure was a retrieval failure. For the question:

> I took a $40 taxi during a business trip. Is it reimbursable, and do I need a receipt?

The system initially retrieved the taxi policy but failed to retrieve the receipt policy. The model therefore correctly said it did not have enough information about receipts. This showed that the failure was in retrieval, not generation.

I added retrieval diagnostics to print retrieved chunk ids and chunk text during evaluation. This made it easier to distinguish:

* retrieval failures,
* generation failures,
* citation failures,
* evaluator brittleness.

To fix retrieval, I added small high-precision retrieval boosts for important policy concepts such as receipt requirements, dollar thresholds, and transportation terms.

A second issue was over-citation. For a dinner reimbursement question, the model sometimes added receipt requirements even though the user did not ask about receipts. This happened because the receipt policy was retrieved as a related but unnecessary chunk. I fixed this in two ways:

1. I updated the prompt to answer only the question asked and avoid adjacent policy facts.
2. I improved retrieval precision by treating domain-generic words such as “business,” “travel,” and “reimbursable” as low-value stopwords.

This reduced irrelevant context and made the model less likely to over-answer.

## Stability Check

I added repeated evaluation on selected hard cases. This helped reveal that the dinner reimbursement case was flaky: sometimes the model cited only the meal policy, and sometimes it also cited the receipt policy. After improving retrieval precision, the selected repeated cases passed in my local runs.

## Final Result

The final system passed the fixed evaluation set and the repeated stability checks in my local runs. The system handles supported answers, insufficient-evidence answers, multi-chunk answers, and citation validation.

## Limitations

This is a small synthetic RAG system. The retriever is keyword-based and would not handle all paraphrases or semantic queries. The retrieval boosts are simple hand-written rules tailored to this small policy corpus.

If I had more time, I would evaluate on a larger policy set, add semantic embeddings, measure retrieval recall separately from answer quality, and test more adversarial cases where irrelevant chunks are highly similar to relevant ones.
