"""
Utils - LLM Prompt Templates
==============================
Optimised prompt templates for use with Mistral 7B and similar
instruction-tuned models.  Each template includes a system preamble,
a structured user instruction, and clearly delimited output format.
"""

from __future__ import annotations

# ── Document Summarisation ────────────────────────────────────────────

SUMMARIZE_PROMPT = """<s>[INST] You are a senior legal analyst. Read the following legal document excerpt and produce a clear, concise summary in 3-5 paragraphs. Focus on:
1. The purpose and subject-matter of the document.
2. Key obligations of each party.
3. Important dates, deadlines, and financial terms.
4. Any notable risks or unusual provisions.

DOCUMENT:
{text}

Provide the summary now. [/INST]"""

# ── Key Term Extraction ───────────────────────────────────────────────

EXTRACT_KEY_TERMS_PROMPT = """<s>[INST] You are a legal terminology expert. Extract the 10-15 most important legal terms, defined phrases, and key concepts from the document below. Return them as a JSON array of strings.

DOCUMENT:
{text}

Return ONLY a JSON array, e.g.: ["term1", "term2", ...] [/INST]"""

# ── Risk Identification ──────────────────────────────────────────────

IDENTIFY_RISKS_PROMPT = """<s>[INST] You are a contract risk analyst. Analyse the following contract clauses and identify potential risks for the contracting party. For each risk:
1. State the clause or provision that poses the risk.
2. Explain why it is risky.
3. Rate the severity as RED (high), YELLOW (medium), or GREEN (low).
4. Suggest an alternative wording or mitigation.

CLAUSES:
{clauses}

Overall Risk Score: {risk_score}/100

Provide a structured risk analysis. [/INST]"""

# ── Clause Comparison ─────────────────────────────────────────────────

COMPARE_CLAUSES_PROMPT = """<s>[INST] You are a legal comparator. Compare the following clauses from different contracts. Identify:
1. Key differences in language and scope.
2. Which version is more favourable to the reader and why.
3. Potential legal implications of the differences.

CLAUSE A ({doc_a_name}):
{clause_a}

CLAUSE B ({doc_b_name}):
{clause_b}

Provide a detailed comparison. [/INST]"""

# ── Recommendations ───────────────────────────────────────────────────

GENERATE_RECOMMENDATIONS_PROMPT = """<s>[INST] You are a senior legal advisor. Based on the analysis below, provide 5-10 actionable recommendations for the contracting party. Each recommendation should be specific and reference the relevant clause.

DOCUMENT SUMMARY:
{summary}

IDENTIFIED CLAUSES:
{clauses}

RISK SCORE: {risk_score}/100
RISK LEVEL: {risk_level}

Provide numbered recommendations. [/INST]"""

# ── RAG Answer Generation ────────────────────────────────────────────

RAG_ANSWER_PROMPT = """<s>[INST] You are a legal document assistant. Answer the user's question using ONLY the context provided below. If the context does not contain enough information, say so. Do not make up facts.

CONTEXT:
{context}

QUESTION:
{question}

Provide a clear, accurate answer. [/INST]"""

# ── Entity Extraction (LLM-assisted) ─────────────────────────────────

ENTITY_EXTRACTION_PROMPT = """<s>[INST] You are a legal entity extractor. From the text below, extract:
1. All party names (organisations and individuals).
2. All dates and deadlines.
3. All monetary amounts with currency.
4. All locations / jurisdictions.

Return the result as a JSON object with keys: "parties", "dates", "amounts", "locations".

TEXT:
{text}

Return ONLY valid JSON. [/INST]"""

# ── Clause Analysis & Scoring ────────────────────────────────────────

CLAUSE_ANALYSIS_PROMPT = """<s>[INST] You are an expert contract risk analyst. Analyze the following {clause_type} clause.
1. Assign a risk score from 0.0 (safest) to 1.0 (most risky).
2. Identify specific obligations in this clause.
3. Explain the risk.

CLAUSE TEXT:
{text}

Return your response ONLY as a JSON object in this format:
{{"risk_score": 0.5, "explanation": "Why it is risky...", "obligations": ["ob 1", "ob 2"]}}
[/INST]"""

# ── Missing Clause Detection ─────────────────────────────────────────

MISSING_CLAUSE_PROMPT = """<s>[INST] You are a legal expert reviewing a contract.
The following standard clause types were found in the contract:
{found_clauses}

Based on standard commercial contracts, identify any critical missing clauses from the following list:
{all_clauses}

Return ONLY a JSON array of missing clause types that represent a significant risk due to their absence.
[/INST]"""

