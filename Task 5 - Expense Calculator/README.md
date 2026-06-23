# Task 5: Expense Claim Tool with LLM Extraction and Deterministic Calculation

This task implements a small travel expense processing tool.

Given a messy natural-language reimbursement request, the system:

1. uses `gpt-5-nano` to extract explicit expense items,
2. normalizes categories and amounts,
3. applies deterministic Python policy rules,
4. returns per-item reimbursement decisions and totals.

The key design principle is:

> The language model extracts structured inputs; Python performs policy calculation.

## Run the tool

From the project root:

```bash
python task5_tool_calc/expense_tool.py
```

## Run evaluation

Run the fixed evaluation set:

```bash
python task5_tool_calc/eval_expense_tool.py
```

Run repeated stability checks:

```bash
python task5_tool_calc/repeat_eval_expense_tool.py
```

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

## Design Notes

The LLM is instructed to extract only:

* `description`
* `category`
* `amount`

It is explicitly told not to calculate reimbursement and not to decide eligibility.

This avoids relying on the model for arithmetic or policy enforcement. The calculator handles caps, eligibility, receipt requirements, and total amounts deterministically.

The implementation includes category normalization for common aliases:

* `cab` → `taxi`
* `Uber` / `Lyft` → `rideshare`
* `subway`, `bus`, `train` → `public_transport`
* `wine`, `beer` → `alcohol`
* `movie` / `movies` → `entertainment`

## Evaluation Strategy

The evaluator checks:

* extracted categories,
* claimed amounts,
* reimbursable amounts,
* receipt requirements,
* eligibility decisions,
* total claimed amount,
* total reimbursable amount.

Hard cases include:

* reimbursement cap boundaries,
* transport aliases,
* non-reimbursable entertainment,
* unknown categories,
* receipt threshold at `$25` versus `$25.01`,
* text that mentions both a claimed amount and a policy cap.

Repeated evaluation is used to check whether LLM extraction instability changes the final calculated result.

## Debugging

`process_expense_claim(..., include_debug=True)` can include the raw extracted items in the output. This helps distinguish extraction failures from deterministic calculation failures.

## Files

* `expense_tool.py`: LLM extraction and deterministic calculation implementation
* `eval_expense_tool.py`: fixed evaluation set
* `repeat_eval_expense_tool.py`: repeated stability checks
* `analysis_report_task5.md`: short write-up of approach, findings, and limitations
