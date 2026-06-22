# Task 2 Report: Order Information Extractor

## Problem

I built a small language-model-based extraction tool for messy order or receipt text. Given unstructured input text, the tool extracts a structured JSON object with the following fields:

* `vendor`
* `order_id`
* `purchase_date`
* `total_usd`
* `items`
* `invoice_email`

The model used is `gpt-5-nano` through the OpenAI API.

## Approach

I started with a simple prompt that defined the target JSON schema and asked the model to return only valid JSON. The prompt instructed the model to use `null` for missing fields, normalize dates to `YYYY-MM-DD`, normalize money amounts to numeric USD values, and avoid inferring details that were not present.

After the baseline worked on a complete order example, I added a parser and schema-normalization layer. This ensures that the extractor always returns the same stable structure, even if the model output is missing fields, contains extra fields, or has minor type inconsistencies. Extra fields are dropped, missing fields are filled with `null` or an empty list, and numeric fields are coerced when possible.

## Evaluation

I used field-level scoring rather than exact JSON matching. Exact matching would be too brittle for extraction tasks because one incorrect field should not make the entire example fail.

The evaluation checks:

* exact or normalized match for scalar fields,
* date normalization,
* numeric tolerance for money amounts,
* `null` handling for missing fields,
* item extraction with normalized item-name matching.

For item extraction, I used semantic normalization for harmless variations such as:

* casing differences,
* singular/plural differences,
* hyphen differences,
* item order differences.

This avoids incorrectly marking semantically correct outputs as failures.

## Hard Cases

I added harder cases to test common extraction failure modes:

* subtotal, tax, shipping, and grand total appearing together,
* multiple emails where only one is the invoice email,
* free gifts that should not be included as purchased items,
* items mentioned without explicit quantities,
* missing order information.

These cases were intended to test whether the model follows the schema and task instructions rather than relying only on obvious keywords.

## Findings and Iterations

The initial extractor performed well on straightforward cases, but item evaluation revealed that exact item-name comparison was too strict. For example, `lunch boxes` and `lunch box` are semantically equivalent in this context. I fixed this by improving the evaluator rather than changing the model prompt, because the model output was correct and the evaluation method was too brittle.

I also added repeated evaluation for selected hard cases. During this process, I found a bug in the repeated-evaluation script: it called the model twice per trial, once to record the output and once to judge pass/fail. This could create false flaky results because the recorded output and the judged output were not necessarily the same. I fixed the evaluator so that pass/fail is computed from the same prediction that is recorded.

After that, I distinguished between surface-form stability and semantic stability. Some outputs varied only in casing or pluralization, but after semantic normalization they were stable and correct.

## Final Result

The final extractor passed the fixed evaluation set with full field accuracy and full item accuracy in my local runs. The repeated stability check also passed on the selected hard cases after evaluator fixes and semantic canonicalization.

## Limitations

The evaluation set is still small and synthetic, so the result should not be interpreted as broad production-level performance. The item-name normalization is heuristic and would not handle all product-name variants. The extractor also assumes USD amounts and a relatively simple order schema.

If I had more time, I would expand the dataset with real receipts, add per-field precision and recall, test more date and currency formats, and evaluate whether a stricter structured-output API would improve format reliability.
