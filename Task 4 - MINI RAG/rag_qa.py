import os
import json
import re
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI


load_dotenv(find_dotenv())

MODEL = "gpt-5-nano"


DOCUMENTS = [
    {
        "id": "P1",
        "text": "Employees may book economy-class flights for domestic business travel. Business-class flights require director approval before booking.",
    },
    {
        "id": "P2",
        "text": "Meals during approved business travel are reimbursable up to $20 for breakfast, $25 for lunch, and $35 for dinner. Alcohol is not reimbursable.",
    },
    {
        "id": "P3",
        "text": "Hotel stays are reimbursable up to $180 per night unless the employee receives written approval from Finance before the trip.",
    },
    {
        "id": "P4",
        "text": "Taxi, rideshare, and public transportation costs are reimbursable when they are directly related to approved business travel.",
    },
    {
        "id": "P5",
        "text": "Expense reports must be submitted within 30 days after the trip ends. Receipts are required for any single expense above $25.",
    },
    {
        "id": "P6",
        "text": "Personal entertainment expenses, including movies, gym passes, sightseeing tours, and minibar charges, are not reimbursable.",
    },
]


def normalize_token(word: str) -> str:
    word = word.lower()

    # Small plural normalization for retrieval.
    if word.endswith("ies"):
        word = word[:-3] + "y"
    elif word.endswith(("ches", "shes", "xes", "zes", "ses")):
        word = word[:-2]
    elif word.endswith("s") and not word.endswith("ss"):
        word = word[:-1]

    return word


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    stopwords = {
        # General English stopwords
        "the", "a", "an", "is", "are", "am", "to", "for", "of", "and",
        "or", "in", "on", "it", "they", "that", "this", "with", "can",
        "i", "my", "do", "does", "be", "was", "were", "if", "during",

        # Domain-generic words that appear in many travel policy chunks
        "expense", "expenses", "reimbursable", "reimburse", "reimbursement",
        "business", "travel", "trip", "approved", "employee", "employees",
        "cost", "costs",
    }

    normalized_words = {
        normalize_token(word)
        for word in words
        if word not in stopwords
    }

    return normalized_words


def retrieval_boost(query: str, doc: dict) -> int:
    """
    Add small high-precision boosts for important policy concepts.
    This helps the simple keyword retriever handle cases where one query
    requires multiple policy chunks.
    """
    query_lower = query.lower()
    doc_lower = doc["text"].lower()

    boost = 0

    # Receipt requirement questions should retrieve the receipt policy.
    if "receipt" in query_lower and "receipt" in doc_lower:
        boost += 3

    # Questions with a dollar amount may need threshold/limit policies.
    if re.search(r"\$\d+", query_lower) and re.search(r"\$\d+", doc_lower):
        boost += 1

    # Transportation questions should retrieve transportation policy.
    transportation_terms = ["taxi", "rideshare", "public transportation"]
    if any(term in query_lower for term in transportation_terms):
        if any(term in doc_lower for term in transportation_terms):
            boost += 3

    return boost


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    query_terms = tokenize(query)

    scored_docs = []
    for doc in DOCUMENTS:
        doc_terms = tokenize(doc["text"])
        lexical_score = len(query_terms.intersection(doc_terms))
        boost_score = retrieval_boost(query, doc)
        score = lexical_score + boost_score

        scored_docs.append((score, doc))

    scored_docs.sort(key=lambda pair: pair[0], reverse=True)

    return [
        doc for score, doc in scored_docs
        if score > 0
    ][:top_k]


def empty_answer() -> dict:
    return {
        "answer": "",
        "cited_chunk_ids": [],
        "enough_evidence": False,
    }


def normalize_answer(data: dict) -> dict:
    if not isinstance(data, dict):
        return empty_answer()

    answer = data.get("answer", "")
    cited_chunk_ids = data.get("cited_chunk_ids", [])
    enough_evidence = data.get("enough_evidence", False)

    if not isinstance(cited_chunk_ids, list):
        cited_chunk_ids = []

    valid_ids = {doc["id"] for doc in DOCUMENTS}
    cited_chunk_ids = [
        str(chunk_id)
        for chunk_id in cited_chunk_ids
        if str(chunk_id) in valid_ids
    ]

    # guardrail: if enough_evidence is False, set cited_chunk_ids to an empty list
    normalized_enough_evidence = bool(enough_evidence)

    if not normalized_enough_evidence:
        cited_chunk_ids = []

    return {
        "answer": str(answer).strip(),
        "cited_chunk_ids": cited_chunk_ids,
        "enough_evidence": normalized_enough_evidence,
    }


def parse_json(raw_text: str) -> dict:
    raw_text = raw_text.strip()

    try:
        return normalize_answer(json.loads(raw_text))
    except json.JSONDecodeError:
        pass

    if raw_text.startswith("```"):
        cleaned = raw_text.strip("`")
        cleaned = cleaned.replace("json\n", "", 1).strip()

        try:
            return normalize_answer(json.loads(cleaned))
        except json.JSONDecodeError:
            pass

    return empty_answer()


def build_context(chunks: list[dict]) -> str:
    lines = []

    for chunk in chunks:
        lines.append(f"[{chunk['id']}] {chunk['text']}")

    return "\n".join(lines)


def answer_question(question: str) -> dict:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    chunks = retrieve(question, top_k=3)
    context = build_context(chunks)

    instructions = """
You answer employee travel reimbursement questions using only the provided policy chunks.

Return only valid JSON in this exact format:
{
  "answer": string,
  "cited_chunk_ids": list of chunk id strings,
  "enough_evidence": boolean
}

Rules:
- Use only the provided policy chunks.
- Answer only the question asked.
- Do not add adjacent policy requirements unless they are necessary to answer the question.
- Cite every chunk that directly supports the answer you give.
- Do not cite chunks that are merely related but not needed for the answer.
- If the chunks do not contain enough information, set enough_evidence to false and say that the policy chunks do not provide enough information.
- Do not use outside knowledge.
- Do not include markdown or explanation outside the JSON.
""".strip()

    input_text = f"""
Policy chunks:
{context}

Question:
{question}
""".strip()

    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=input_text,
    )

    result = parse_json(response.output_text)

    # Citation guardrail: only allow citations from chunks that were actually
    # retrieved and shown to the model.
    retrieved_ids = {chunk["id"] for chunk in chunks}
    result["cited_chunk_ids"] = [
        chunk_id
        for chunk_id in result.get("cited_chunk_ids", [])
        if chunk_id in retrieved_ids
    ]

    # Simple guardrail: if retrieval found no chunks, force insufficient evidence.
    if not chunks:
        result["answer"] = "The provided policy chunks do not contain enough information to answer this question."
        result["cited_chunk_ids"] = []
        result["enough_evidence"] = False

    return result


if __name__ == "__main__":
    questions = [
        "Can I expense dinner during a business trip?",
        "Can I book a business-class flight?",
        "Are minibar charges reimbursable?",
        "Can I expense a new laptop?",
    ]

    for question in questions:
        print("=" * 70)
        print(f"Question: {question}")
        result = answer_question(question)
        print(json.dumps(result, indent=2, ensure_ascii=False))