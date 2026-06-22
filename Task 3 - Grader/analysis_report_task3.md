# Task 3 Report: LLM-as-Judge Rubric Grader

## Problem

I built a small language-model-based grading tool. Given a user question and a candidate answer, the tool scores the answer on five dimensions:

* `accuracy`
* `completeness`
* `clarity`
* `safety`
* `overall`

Each score is an integer from 1 to 5. The tool also returns short feedback explaining the main issue or strength of the answer.

The model used is `gpt-5-nano` through the OpenAI API.

## Approach

I started with a rubric-based prompt that defines each scoring dimension. The model is instructed to return only valid JSON with the five scores and a short feedback string.

I added a parser and normalization layer to make sure the output has a stable schema. Invalid or missing scores are converted to `null`, and feedback is normalized to a string.

The main challenge was not JSON formatting, but score calibration. In early evaluation, some failures came from ambiguity in the rubric rather than from model inability. For example, an answer that gives four reasons when the user asked for exactly two should be penalized for completeness, not safety. Similarly, a legally cautious answer may be incomplete without being factually inaccurate.

I refined the rubric to clearly separate:

* factual correctness from completeness,
* instruction following from safety,
* incompleteness from inaccuracy,
* unsafe certainty from cautious uncertainty.

## Evaluation

Because grading is subjective, I did not require exact score matches. Instead, I used expected score ranges for the dimensions that mattered in each test case.

The evaluation set included:

* strong answers,
* partially correct answers,
* irrelevant answers,
* factually incorrect answers,
* unsafe medical advice,
* safe medical advice,
* fluent answers that violate instructions,
* overconfident legal advice,
* cautious legal advice.

Each test case only checks the dimensions that are relevant to that case. For example, the HTTP 404 case primarily checks that accuracy and overall are low; it does not require a strict safety score because the main issue is factual accuracy, not user safety.

## Consistency Check

I added an overall consistency check to catch clearly incoherent grades. For example, if an answer has very low accuracy or safety, the overall score should not be high even if the answer is clear.

The consistency check is intentionally simple:

* if accuracy is very low, overall cannot be high;
* if safety is very low, overall cannot be high;
* overall should not exceed the weakest key dimension by too much.

This gives the system a lightweight engineering guardrail instead of relying entirely on the model's self-consistency.

## Stability Check

I also added repeated evaluation for selected hard cases. Since LLM-as-judge scoring is inherently subjective, I did not require every run to produce identical scores. Instead, I checked whether repeated runs stayed within acceptable ranges and whether the overall score remained consistent with the dimension scores.

The repeated evaluation passed on the selected hard cases in my local runs.

## Findings and Iterations

The most important finding was that failures in grader tasks can come from three different sources:

1. the model judge is wrong,
2. the rubric is ambiguous,
3. the evaluation expectation is too rigid.

Several early failures were caused by overly strict expected ranges rather than actual judge failures. I adjusted the evaluation to check the key judgment for each case instead of over-constraining every score.

I also refined the rubric to prevent dimension confusion. For example, violating “exactly two reasons” is a completeness issue, not a safety issue. A cautious legal answer can be accurate and safe even if it lacks jurisdiction-specific details.

## Final Result

The final grader passed the fixed evaluation set and repeated stability checks in my local runs. The output is structured, score ranges are calibrated, and the consistency check catches obviously incoherent overall scores.

## Limitations

This is still a small synthetic evaluation set. The scores should not be interpreted as fully calibrated human judgment. The rubric is also task-specific and would need adjustment for other domains.

If I had more time, I would compare the judge scores against human annotations, measure inter-run variance over a larger set, add more high-risk safety cases, and consider using pairwise ranking in addition to absolute 1–5 scores.
