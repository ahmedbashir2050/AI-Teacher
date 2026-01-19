import json
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("audit")


def log_audit(
    user_id: str,
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    status: str = "success",
    metadata: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
):
    """
    Standardized audit logging for production security and compliance.
    """
    audit_entry = {
        "timestamp": time.time(),
        "service_name": "api-gateway",
        "event_type": "audit",
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "status": status,
        "metadata": metadata or {},
        "request_id": request_id,
    }
    logger.info(f"AUDIT_EVENT: {json.dumps(audit_entry)}")
