# 90-Minute Applied AI Coding Assessment Playbook

## Goal

Build a small language-model-based tool, evaluate it, refine it based on failures, and write up the findings.

The goal is not to build a perfect system. The goal is to show sound engineering judgment under time pressure.

## Core Principles

1. Follow the scenario closely.
2. Do not change the required model.
3. Start with the simplest working baseline.
4. Create an evaluation harness early.
5. Improve based on observed failures, not guesses.
6. Prefer conservative fixes over broad overfitting.
7. Leave time for a short write-up.

## Timeline

### 0–10 min: Understand the task

Read the prompt carefully and identify:

* What is the input?
* What is the required output?
* What format is expected?
* What model must be used?
* Are there visible test cases?
* What hidden test cases might check?

Write down the task in one sentence.

Example:

> Given a user message, classify it into exactly one allowed category.

Then define the output labels or fields clearly.

### 10–25 min: Build the baseline

Implement the simplest working version:

* call `gpt-5-nano` through the provided OpenAI client,
* write a clear prompt,
* return the required output,
* add minimal validation.

Do not optimize yet.

The first milestone is:

> The code runs end-to-end on 2–3 examples.

### 25–40 min: Build evaluation

Create a small evaluation script with labeled cases.

Include:

* straightforward examples,
* edge cases,
* ambiguous cases,
* misleading keyword cases.

Measure simple accuracy first.

For each failure, print:

* input,
* expected output,
* predicted output.

The second milestone is:

> I can see exactly what failed and why.

### 40–60 min: Refine based on failures

Use failure analysis to improve the system.

Possible improvements:

* clarify label definitions,
* add tie-breaking rules,
* require JSON output,
* add parser fallback,
* add conservative deterministic overrides.

Avoid broad rules that only memorize visible tests.

Good rule:

> If the message reports data exposure or security bypass, classify as `safety_concern`.

Risky rule:

> If the message contains the word “login,” always classify as `account_access`.

The third milestone is:

> The system improves on observed failures without obviously overfitting.

### 60–70 min: Check robustness

Run the evaluation again.

For ambiguous cases, consider repeated evaluation if time allows.

This helps detect unstable model behavior.

Useful categories:

* stable pass,
* flaky,
* stable fail.

If a case is flaky, decide whether the taxonomy needs a clearer tie-breaking rule.

### 70–82 min: Write up findings

Write a short report covering:

* problem,
* approach,
* evaluation method,
* failures found,
* changes made,
* final result,
* limitations.

Keep it concise and honest.

Do not claim broad real-world performance from a small test set.

### 82–90 min: Final cleanup

Before submitting:

* run the evaluation one final time,
* check that the required model has not been changed,
* check that API keys are not hardcoded,
* ensure the main files are named clearly,
* make sure the report matches what the code actually does.

## Minimal Submission Structure

Recommended files:

* main implementation file
* evaluation script
* short report
* README if time allows

## Common Mistakes to Avoid

* Spending too long on architecture before the first working version.
* Only testing easy examples.
* Optimizing only for visible tests.
* Ignoring output parsing and validation.
* Changing the required model.
* Forgetting to write up what was learned.
* Claiming the system is robust without evidence.

## Good Engineering Signals

Strong submissions usually show:

* a simple baseline,
* clear task framing,
* explicit assumptions,
* meaningful evaluation cases,
* failure-driven iteration,
* conservative fixes,
* honest limitations,
* readable code.
