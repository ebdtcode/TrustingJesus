"""Client identification, audit logging, and role-based access.

Azure Function keys handle authentication (is this request allowed at all?).
This module handles authorization (what is this client allowed to do?) and
audit logging (who did what?).

Clients identify themselves via the X-Client-ID header. Authorized clients
and their roles are stored in the AUTHORIZED_CLIENTS app setting as JSON.

Roles:
  admin      — Full access: process, scan, configure
  processor  — Can process videos and scan channels
  scanner    — Can scan channels but not auto-process
  viewer     — Can only read health/status

If AUTHORIZED_CLIENTS is not set, all authenticated requests (those with a
valid function key) are allowed with full access. This preserves backward
compatibility with the existing single-key setup.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Optional

import azure.functions as func

logger = logging.getLogger(__name__)

ROLE_HIERARCHY = {
    "admin": 4,
    "processor": 3,
    "scanner": 2,
    "viewer": 1,
}

ENDPOINT_REQUIRED_ROLE = {
    "process": "processor",
    "scan": "scanner",
    "status": "viewer",
    "health": "viewer",
}


@dataclass
class ClientInfo:
    client_id: str
    name: str
    role: str

    def has_role(self, required_role: str) -> bool:
        return ROLE_HIERARCHY.get(self.role, 0) >= ROLE_HIERARCHY.get(
            required_role, 0
        )


def identify_client(req: func.HttpRequest) -> Optional[ClientInfo]:
    """Identify the client from the X-Client-ID header.

    Returns ClientInfo if AUTHORIZED_CLIENTS is configured and the client
    is found. Returns None if AUTHORIZED_CLIENTS is not set (open access mode).
    """
    clients_json = os.environ.get("AUTHORIZED_CLIENTS", "")
    if not clients_json:
        return None  # Open access mode

    client_id = req.headers.get("X-Client-ID", "")
    if not client_id:
        return ClientInfo(client_id="anonymous", name="Anonymous", role="viewer")

    try:
        clients = json.loads(clients_json)
    except json.JSONDecodeError:
        logger.error("AUTHORIZED_CLIENTS is not valid JSON")
        return None

    client_data = clients.get(client_id)
    if not client_data:
        logger.warning("Unknown client ID: %s", client_id)
        return ClientInfo(client_id=client_id, name="Unknown", role="viewer")

    return ClientInfo(
        client_id=client_id,
        name=client_data.get("name", client_id),
        role=client_data.get("role", "viewer"),
    )


def check_access(
    req: func.HttpRequest, endpoint: str
) -> Optional[func.HttpResponse]:
    """Check if the request is authorized for the given endpoint.

    Returns None if access is granted, or an HTTP 403 response if denied.
    """
    client = identify_client(req)

    if client is None:
        # Open access mode (AUTHORIZED_CLIENTS not configured)
        _log_access(req, endpoint, "open-access", granted=True)
        return None

    required_role = ENDPOINT_REQUIRED_ROLE.get(endpoint, "admin")

    if client.has_role(required_role):
        _log_access(req, endpoint, client.client_id, granted=True)
        return None

    _log_access(req, endpoint, client.client_id, granted=False)
    return func.HttpResponse(
        json.dumps(
            {
                "error": "Forbidden",
                "detail": f"Client '{client.name}' with role '{client.role}' "
                f"cannot access '{endpoint}' (requires '{required_role}')",
            }
        ),
        status_code=403,
        mimetype="application/json",
    )


def _log_access(
    req: func.HttpRequest,
    endpoint: str,
    client_id: str,
    granted: bool,
):
    """Log access attempts for audit trail."""
    status = "GRANTED" if granted else "DENIED"
    logger.info(
        "ACCESS %s: client=%s endpoint=%s method=%s",
        status,
        client_id,
        endpoint,
        req.method,
    )
