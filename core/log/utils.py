import json
import logging
from typing import Any, Optional, Tuple
from fastapi import Request
from core.utils.sm2_crypto_util import hash_with_salt
from core.utils.trace_utils import get_trace_id

logger = logging.getLogger(__name__)


class TraceIdFilter(logging.Filter):
    """Logging filter that adds trace_id to every log record.

    Usage::

        logging.getLogger().addFilter(TraceIdFilter())

    This mirrors Snowy's CustomTraceIdConverter which inserts ``[traceId]``
    into log output via a Logback conversion word.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        trace_id = get_trace_id()
        record.trace_id = trace_id if trace_id else "-"
        return True


def parse_user_agent(user_agent: Optional[str]) -> Tuple[str, str]:
    """Parse User-Agent string to extract browser and OS info."""
    from core.utils.user_agent_utils import get_browser, get_os
    return get_browser(user_agent), get_os(user_agent)


_EXCLUDE_PARAMS = frozenset({"request", "db", "file"})


def extract_params_json(request: Request, func_kwargs: dict) -> str:
    """Extract request parameters as JSON, excluding infrastructure params."""
    try:
        if request.method in ("POST", "PUT", "PATCH"):
            filtered = {}
            for k, v in func_kwargs.items():
                if k in _EXCLUDE_PARAMS or v is None:
                    continue
                try:
                    json.dumps(v)
                    filtered[k] = v
                except (TypeError, ValueError):
                    filtered[k] = str(v)
            return json.dumps(filtered, ensure_ascii=False, default=str) if filtered else ""
        return ""
    except Exception:
        return ""


def get_result_json(result: Any) -> Optional[str]:
    """Serialize the result to JSON string."""
    if result is None:
        return None
    try:
        # FastAPI routes often return Result objects with model_dump
        if hasattr(result, 'model_dump'):
            return json.dumps(result.model_dump(), ensure_ascii=False, default=str)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception:
        return str(result)


def generate_log_signature(op_data: dict) -> str:
    """Generate SM3-based signature for log tamper-proofing."""
    try:
        content = json.dumps(op_data, sort_keys=True, ensure_ascii=False, default=str)
        return hash_with_salt(content, "hei-log-sign")
    except Exception as e:
        logger.warning(f"Failed to generate log signature: {e}")
        return ""
