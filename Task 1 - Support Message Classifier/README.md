# Support Message Classifier

This project implements a small language-model-based classifier for user support messages.

Given a user message, the tool assigns one label from:

* `bug_report`
* `feature_request`
* `pricing_question`
* `account_access`
* `safety_concern`
* `irrelevant`

The model is `gpt-5-nano` through the OpenAI API.

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```bash
OPENAI_API_KEY=your_api_key_here
```

## Run the classifier

```bash
python classify.py
```

## Run evaluation

Run the fixed evaluation set:

```bash
python eval_classifier.py
```

Run repeated stability checks on ambiguous cases:

```bash
python repeat_eval.py
```

## Design notes

The classifier uses a language model for semantic classification, then applies conservative deterministic overrides for high-confidence tie-breaking cases.

The main engineering issue was not basic classification, but ambiguity between overlapping labels. For example:

* refund + slow app performance
* login/password problems vs product bugs
* explicit improvement requests vs bug reports
* security/privacy concerns vs ordinary account access

To handle this, I used:

1. explicit label definitions,
2. tie-breaking rules in the prompt,
3. JSON output parsing with fallback,
4. conservative deterministic overrides,
5. fixed evaluation cases,
6. repeated evaluation for selected ambiguous cases.

## Files

* `classify.py`: classifier implementation
* `eval_classifier.py`: fixed labeled evaluation set
* `repeat_eval.py`: repeated stability evaluation
* `analysis_report.md`: short write-up of approach, findings, and limitations
* `requirements.txt`: Python dependencies
