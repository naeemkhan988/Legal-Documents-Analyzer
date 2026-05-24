"""
Utils - Constants & Enumerations
=================================
Application-wide constants, enumerations, and default values.
"""

from __future__ import annotations

from enum import Enum


# ── Clause Types ──────────────────────────────────────────────────────

class ClauseType(str, Enum):
    LIABILITY_LIMITATION = "liability_limitation"
    TERMINATION = "termination"
    PAYMENT_TERMS = "payment_terms"
    CONFIDENTIALITY = "confidentiality"
    INDEMNIFICATION = "indemnification"
    WARRANTIES = "warranties"
    LIMITATION_OF_LIABILITY = "limitation_of_liability"
    FORCE_MAJEURE = "force_majeure"
    SEVERABILITY = "severability"
    GOVERNING_LAW = "governing_law"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    NON_COMPETE = "non_compete"
    DISPUTE_RESOLUTION = "dispute_resolution"
    ASSIGNMENT = "assignment"


ALL_CLAUSE_TYPES: list[str] = [ct.value for ct in ClauseType]


# ── Risk Levels ───────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


# ── Supported File Types ─────────────────────────────────────────────

SUPPORTED_FILE_TYPES: set[str] = {"pdf", "docx", "txt"}
SUPPORTED_MIME_TYPES: dict[str, str] = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}


# ── Report Formats ───────────────────────────────────────────────────

class ReportFormat(str, Enum):
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    EXCEL = "excel"


# ── API Response Messages ────────────────────────────────────────────

class Messages:
    DOCUMENT_UPLOADED = "Document uploaded and processed successfully."
    DOCUMENT_DELETED = "Document deleted successfully."
    DOCUMENT_NOT_FOUND = "Document not found."
    ANALYSIS_STARTED = "Analysis started."
    ANALYSIS_COMPLETE = "Analysis completed successfully."
    ANALYSIS_NOT_FOUND = "No analysis found for this document."
    REPORT_GENERATED = "Report generated successfully."
    REPORT_NOT_FOUND = "Report not found."
    COMPARISON_COMPLETE = "Comparison completed successfully."
    SEARCH_COMPLETE = "Search completed."
    INVALID_FILE_TYPE = "Unsupported file type. Accepted: PDF, DOCX, TXT."
    FILE_TOO_LARGE = "File exceeds the maximum allowed size."
    INTERNAL_ERROR = "An internal error occurred. Please try again."
    LLM_UNAVAILABLE = "LLM service is currently unavailable."


# ── Default Configurations ───────────────────────────────────────────

DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 50
DEFAULT_TOP_K = 5
MAX_DOCUMENT_TEXT_LENGTH = 500_000  # characters
DEFAULT_USER_ID = "default_user"  # used when auth is disabled
