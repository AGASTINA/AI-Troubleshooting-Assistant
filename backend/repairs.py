"""Fixed, user-confirmed Windows repair actions. Never accepts executable input."""

import os
import platform
import subprocess
from pathlib import Path

REPAIR_CATALOG = {
    "flush_dns_cache": {
        "id": "flush_dns_cache",
        "title": "Flush the DNS cache",
        "description": "Clears cached name lookups. It does not change network settings or delete files.",
    },
    "reset_store_cache": {
        "id": "reset_store_cache",
        "title": "Reset Microsoft Store cache",
        "description": "Opens the built-in Store cache reset utility. It does not remove installed apps or account data.",
    },
}


def suggested_repairs(category: str, message: str) -> list[dict]:
    if platform.system() != "Windows":
        return []
    if category == "network":
        return [dict(REPAIR_CATALOG["flush_dns_cache"])]
    if category == "application" and "store" in message.lower():
        return [dict(REPAIR_CATALOG["reset_store_cache"])]
    return []


def execute_repair(repair_id: str, confirmed: bool) -> tuple[dict, int]:
    if confirmed is not True:
        return {"error": "Explicit confirmation is required before running a repair."}, 400
    if repair_id not in REPAIR_CATALOG:
        return {"error": "Repair action not found."}, 404
    if platform.system() != "Windows":
        return {"error": "This repair is available only on Windows."}, 501

    if repair_id == "flush_dns_cache":
        try:
            result = subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            return {"error": "The DNS cache repair timed out."}, 504
        except OSError:
            return {"error": "Windows could not start the DNS cache repair."}, 500
        if result.returncode != 0:
            return {"error": "Windows could not complete the DNS cache repair."}, 500
        return {"status": "completed", "message": "The DNS cache was flushed successfully."}, 200

    store_reset = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "wsreset.exe"
    if not store_reset.is_file():
        return {"error": "The Microsoft Store reset utility was not found."}, 404
    try:
        subprocess.Popen([str(store_reset)], close_fds=True)
    except OSError:
        return {"error": "Windows could not start the Microsoft Store reset utility."}, 500
    return {"status": "started", "message": "The Microsoft Store cache reset utility was opened."}, 200