"""Constantes de la aplicación (límites, enums, valores por defecto).

Placeholder inicial — sin lógica todavía.
"""

from enum import Enum


class UploadStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    RESTORATION = "restoration"
    ENHANCEMENT = "enhancement"
    UPSCALE = "upscale"
    INPAINT = "inpaint"
    STYLE = "style"


class WorkflowMode(str, Enum):
    """Modo de restauración: Epic (SD1.5 rápido) o Flux Kontext (calidad superior)."""

    EPIC = "epic"
    FLUX = "flux"


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROK = "grok"


class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# --- Rate limiting -----------------------------------------------------------
DEFAULT_RATE_LIMIT_PER_MINUTE = 100

# --- Defaults de subscription ------------------------------------------------
DEFAULT_CREDITS_BALANCE = 100
DEFAULT_MONTHLY_UPLOADS_LIMIT = 10
