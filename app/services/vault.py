from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken

VAULT_VERSION_DUAL = 2


def _master_fernet() -> Fernet:
    key = os.getenv("FERNET_KEY")
    if not key:
        key = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")
        os.environ["FERNET_KEY"] = key
    return Fernet(key.encode("utf-8"))


def _vault_master_secret() -> str:
    _master_fernet()
    return os.getenv("VAULT_MASTER_SECRET") or os.getenv("FERNET_KEY") or "vault-dev-secret"


def _derive_user_fernet(user_id: str) -> Fernet:
    digest = hashlib.sha256(f"{_vault_master_secret()}:{user_id}".encode("utf-8")).digest()
    user_key = base64.urlsafe_b64encode(digest)
    return Fernet(user_key)


def get_fernet() -> Fernet:
    return _master_fernet()


def rotate_audit_log_if_needed(path: str) -> None:
    if not path or not os.path.exists(path):
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        return

    try:
        current_size = os.path.getsize(path)
    except OSError:
        current_size = 0

    max_bytes = int(os.getenv("PURGE_AUDIT_MAX_BYTES", "1048576").strip() or "1048576")
    interval_seconds = int(os.getenv("PURGE_AUDIT_ROTATION_INTERVAL_SECONDS", "0").strip() or "0")

    should_rotate_by_size = max_bytes > 0 and current_size >= max_bytes
    should_rotate_by_interval = False
    if interval_seconds > 0:
        try:
            modified_at = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
            should_rotate_by_interval = (datetime.now(timezone.utc) - modified_at).total_seconds() >= interval_seconds
        except OSError:
            should_rotate_by_interval = False

    if not should_rotate_by_size and not should_rotate_by_interval:
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    shutil.copy2(path, f"{path}.{timestamp}")
    with open(path, "w", encoding="utf-8"):
        pass


def seal_payload(user_id: str, payload: Dict[str, Any]) -> str:
    _master_fernet()
    serialized = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    user_cipher = _derive_user_fernet(user_id).encrypt(serialized).decode("utf-8")
    envelope = {
        "vault_version": VAULT_VERSION_DUAL,
        "user_id": user_id,
        "user_cipher": user_cipher,
    }
    return _master_fernet().encrypt(json.dumps(envelope, ensure_ascii=False).encode("utf-8")).decode("utf-8")


def unseal_payload(user_id: str, token: str) -> Dict[str, Any]:
    try:
        outer = json.loads(_master_fernet().decrypt(token.encode("utf-8")).decode("utf-8"))
    except InvalidToken as exc:
        raise ValueError("Unable to decrypt vault token") from exc

    if isinstance(outer, dict) and outer.get("vault_version") == VAULT_VERSION_DUAL:
        if outer.get("user_id") != user_id:
            raise ValueError("Vault user mismatch")
        inner = _derive_user_fernet(user_id).decrypt(outer["user_cipher"].encode("utf-8"))
        return json.loads(inner.decode("utf-8"))

    if isinstance(outer, dict):
        return outer
    raise ValueError("Invalid vault payload format")


def audit_log_path() -> str:
    return os.getenv("SECURITY_AUDIT_LOG_PATH", os.getenv("PURGE_AUDIT_LOG_PATH", "security_audit.jsonl"))


def write_audit_event(
    action_type: str,
    user_id: str,
    metadata: Optional[Dict[str, Any]] = None,
    actor: str = "system",
) -> None:
    path = audit_log_path()
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    rotate_audit_log_if_needed(path)

    entry = {
        "user_id": user_id,
        "action_type": action_type,
        "actor": actor,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {},
    }
    encrypted_entry = _master_fernet().encrypt(json.dumps(entry, separators=(",", ":")).encode("utf-8")).decode("utf-8")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(encrypted_entry + "\n")
