# Task 1 Report: Support Message Classifier

## Problem

I built a small language-model-based classifier for user support messages. Given a user message, the tool assigns exactly one label from the following taxonomy:

* `bug_report`
* `feature_request`
* `pricing_question`
* `account_access`
* `safety_concern`
* `irrelevant`

The model used is `gpt-5-nano` through the OpenAI API.

## Approach

I started with a direct prompt that described each label and asked the model to return one classification. After the initial version worked on straightforward examples, I added a small evaluation harness with both simple and ambiguous test cases.

The main challenge was not basic classification, but tie-breaking between overlapping categories. For example, a message may mention both a refund and slow app performance, or both login behavior and a possible bug. I refined the prompt to include explicit tie-breaking rules.

I also added conservative deterministic post-processing rules. The model handles broad semantic classification, while deterministic overrides handle high-confidence cases where the taxonomy has clear priority rules. For example, security and data exposure issues are always classified as `safety_concern`, and explicit refund or invoice requests are classified as `pricing_question` unless the message is clearly about broken product behavior.

Finally, I changed the model output to JSON and added a parser fallback. This makes the tool more robust if the model returns extra text or slightly malformed output.

## Evaluation

I used two evaluation scripts:

1. `eval_classifier.py` checks accuracy on a fixed set of labeled test cases.
2. `repeat_eval.py` runs selected ambiguous cases multiple times to check stability.

The evaluation cases included straightforward examples, ambiguous examples, and adversarial examples with misleading keywords.

Examples of ambiguous cases included:

* `Can I get a refund? Also, the app is very slow.`
* `The billing page crashes when I try to update my card.`
* `The login page says my password is wrong, but I can sign in on mobile.`
* `Could you make the dashboard faster? It takes 20 seconds to load.`

## Findings and Iterations

The initial version passed simple examples, but one ambiguous case showed unstable behavior across repeated runs:

`Can I get a refund? Also, the app is very slow.`

The model sometimes classified it as `pricing_question` and sometimes as `bug_report`. This revealed that one-off accuracy can hide unstable behavior. I handled this by making the tie-breaking rule explicit: when the user makes an explicit refund, billing, invoice, or payment request, classify it as `pricing_question` unless the main issue is clearly security-related or broken product behavior.

After this, additional failures exposed other boundary cases:

* Login/password problems could be mistaken for bugs.
* Explicit improvement requests such as “Could you make the dashboard faster?” could be mistaken for bug reports because they mention poor performance.

I addressed these with conservative post-processing rules based on clear textual signals, while avoiding overly broad keyword rules that would overfit to visible tests.

## Final Result

After prompt refinement, JSON parsing, fallback handling, deterministic overrides, and repeated evaluation, the classifier passed the visible evaluation set (28/28) and the selected repeated stability checks in my local runs (6/6, all stable pass).

## Limitations

This is still a small classifier, not a complete production system. The deterministic rules are intentionally conservative, but they may miss cases phrased in unexpected ways. The evaluation set is also small, so the reported accuracy should not be interpreted as broad real-world performance.

If I had more time, I would expand the evaluation set, include more realistic support messages, track per-label precision and recall, and test stability over a larger set of ambiguous inputs. I would also consider separating multi-intent messages into primary and secondary labels if the product scenario required it.
