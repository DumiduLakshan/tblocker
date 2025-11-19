from __future__ import annotations

import base64
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

LICENSE_API_URL = os.getenv("TBLOCK_LICENSE_API", "https://tblock-licence-api-t4cao.ondigitalocean.app/verify"")
LICENSE_CACHE = Path("/etc/tblock/license")
PAYLOAD_FILE = Path(__file__).with_name("payload.bin")
INSTALL_ROOT = Path("/opt/tblockguard")


def load_cached_key() -> str | None:
    if LICENSE_CACHE.exists():
        try:
            return LICENSE_CACHE.read_text().strip()
        except Exception:
            return None
    return None


def save_cached_key(key: str) -> None:
    try:
        LICENSE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        LICENSE_CACHE.write_text(key)
    except Exception:
        pass


def fetch_payload_key(license_key: str) -> bytes:
    resp = requests.post(
        LICENSE_API_URL,
        json={"license_key": license_key},
        timeout=10,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"License server rejected key ({resp.status_code}): {resp.text}"
        )
    data = resp.json()
    if not data.get("allowed"):
        raise RuntimeError("License server denied access.")
    payload_key = data.get("payload_key")
    if not payload_key:
        raise RuntimeError("License server did not return a payload key.")
    return base64.b64decode(payload_key)


def decrypt_payload(payload_key: bytes) -> bytes:
    blob = PAYLOAD_FILE.read_bytes()
    nonce, ciphertext = blob[:12], blob[12:]
    aesgcm = AESGCM(payload_key)
    return aesgcm.decrypt(nonce, ciphertext, None)


def run_installer(archive_bytes: bytes) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        archive_path = tmp_path / "payload.zip"
        archive_path.write_bytes(archive_bytes)
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(tmp_path)
        staging = tmp_path / "payload"
        staging.mkdir()
        for item in tmp_path.iterdir():
            if item.name in {"payload.zip", "payload"}:
                continue
            target = staging / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
        if INSTALL_ROOT.exists():
            shutil.rmtree(INSTALL_ROOT)
        shutil.copytree(staging, INSTALL_ROOT)
        installer = INSTALL_ROOT / "install.py"
        if not installer.exists():
            raise RuntimeError("Decrypted payload missing install.py")
        subprocess.run([sys.executable, str(installer)], check=True, cwd=INSTALL_ROOT)


def main() -> int:
    cached = load_cached_key()
    prompt = "Enter license key"
    if cached:
        prompt += f" [{cached}]"
    prompt += ": "
    license_key = input(prompt).strip() or cached
    if not license_key:
        print("License key required.")
        return 1
    payload_key = fetch_payload_key(license_key)
    archive_bytes = decrypt_payload(payload_key)
    save_cached_key(license_key)
    run_installer(archive_bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
