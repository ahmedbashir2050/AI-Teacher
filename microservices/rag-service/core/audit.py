import logging
import json
import time
from typing import Any, Dict, Optional

# The main logger is already configured for JSON in core/observability.py
logger = logging.getLogger("audit")

def log_audit(
    user_id: str,
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    status: str = "success",
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
):
    """
    Standardized audit logging for production security and compliance.
    """
    audit_entry = {
        "timestamp": time.time(),
        "event_type": "audit",
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "status": status,
        "details": details or {},
        "request_id": request_id
    }
    # This will be picked up by the JSON formatter configured in observability.py
    logger.info(f"AUDIT_EVENT: {json.dumps(audit_entry)}")
