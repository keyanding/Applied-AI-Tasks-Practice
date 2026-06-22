# Task 2: Order Information Extractor

This task implements a small language-model-based structured extraction tool.

Given messy order or receipt text, the tool extracts:

* `vendor`
* `order_id`
* `purchase_date`
* `total_usd`
* `items`
* `invoice_email`

The model is `gpt-5-nano` through the OpenAI API.

## Run the extractor

From the project root:

```bash
python task2_extractor/extract_order.py
```

## Run evaluation

Run the fixed evaluation set:

```bash
python task2_extractor/eval_extractor.py
```

Run repeated stability checks:

```bash
python task2_extractor/repeat_eval_extractor.py
```

## Design Notes

The extractor asks the model to return JSON, then normalizes the result into a stable schema. Missing fields are filled with `null` or an empty list, extra fields are dropped, and numeric fields are coerced when possible.

The evaluation uses field-level scoring rather than exact JSON matching. This is important because extraction outputs can be partially correct.

For item extraction, the evaluator tolerates harmless variations such as:

* casing differences,
* singular/plural differences,
* hyphen differences,
* item order differences.

The repeated evaluation script checks selected hard cases for stability and distinguishes meaningful semantic differences from harmless surface-form variation.

## Files

* `extract_order.py`: extraction implementation
* `eval_extractor.py`: fixed evaluation set with field-level and item-level scoring
* `repeat_eval_extractor.py`: repeated stability checks
* `analysis_report_task2.md`: short write-up of approach, findings, and limitations
