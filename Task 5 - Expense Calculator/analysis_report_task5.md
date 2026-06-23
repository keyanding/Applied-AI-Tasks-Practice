# Task 5 Report: Expense Claim Tool with LLM Extraction and Deterministic Calculation

## Problem

I built a small travel expense processing tool. Given a messy natural-language reimbursement request, the tool extracts explicit expense items and then calculates the reimbursable amount according to a fixed policy.

The model used is `gpt-5-nano` through the OpenAI API.

## Approach

I separated the task into two parts:

1. LLM-based extraction
2. Deterministic policy calculation

The language model extracts only structured expense items:

* `description`
* `category`
* `amount`

The model is explicitly instructed not to calculate reimbursement and not to decide eligibility. Those decisions are handled by Python code.

This separation is important because reimbursement caps, eligibility rules, and receipt thresholds are deterministic policy rules. They should not depend on the model's reasoning or arithmetic.

## Policy Rules

The deterministic calculator applies these rules:

* breakfast is capped at `$20`
* lunch is capped at `$25`
* dinner is capped at `$35`
* hotel is capped at `$180`
* taxi, rideshare, and public transport are fully reimbursable
* alcohol, minibar, and entertainment are not reimbursable
* unknown categories are not reimbursable
* receipts are required only when a single expense is greater than `$25`

The final output includes per-item eligibility, reimbursable amount, receipt requirement, and the total claimed and reimbursable amounts.

## Evaluation

I evaluated the final processed result, including:

* extracted categories,
* claimed amounts,
* reimbursable amounts,
* receipt requirements,
* eligibility decisions,
* total claimed amount,
* total reimbursable amount.

The evaluation includes straightforward and harder cases:

* mixed meal, taxi, and alcohol claims,
* meal reimbursement caps,
* hotel cap and minibar exclusion,
* unknown category handling,
* receipt threshold boundary at `$25` vs `$25.01`,
* transport aliases such as Uber, cab, subway, and bus,
* cases where the text mentions both a claimed amount and a reimbursement cap.

## Findings and Iterations

The key engineering decision was to avoid letting the model perform policy calculation. For example, if the input says:

> I paid $50 for dinner. I know the cap is $35, but I am claiming the full $50 expense.

The model should extract the claimed expense as `$50`, not `$35`. The Python calculator then applies the dinner cap and computes `$35` as the reimbursable amount.

I also added category normalization for common aliases such as:

* `cab` → `taxi`
* `Uber` / `Lyft` → `rideshare`
* `subway`, `bus`, `train` → `public_transport`
* `wine`, `beer` → `alcohol`
* `movie` / `movies` → `entertainment`

This makes the model's extraction more robust without relying on the model to perfectly choose the final policy category.

I added repeated evaluation on hard cases to check whether extraction instability caused final-result instability. The selected repeated cases passed in my local runs.

Finally, I added a debug mode that can include the raw extracted items. This makes it easier to diagnose whether a failure comes from extraction, calculation, or evaluation.

## Final Result

The final tool passed the fixed evaluation set and repeated stability checks in my local runs. The system keeps model judgment and deterministic policy logic separate, which makes the result easier to test and debug.

## Limitations

This is a small synthetic task. The extraction categories are limited, and the policy rules are simplified. The hotel rule assumes a single-night amount rather than parsing multiple nights. The system also assumes all amounts are in USD.

If I had more time, I would add more realistic receipts, multi-night hotel cases, currency handling, per-item business-purpose extraction, and separate evaluation of extraction accuracy versus calculation accuracy.
