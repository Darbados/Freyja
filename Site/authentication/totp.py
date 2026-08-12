import base64
import hashlib
import hmac
import io
import secrets
import struct
import time
from urllib.parse import quote, urlencode

from cryptography.fernet import Fernet
from django.conf import settings
import qrcode


TOTP_DIGITS = 6
TOTP_INTERVAL = 30


def generate_secret() -> str:
    """Returns a 160-bit Base32 secret compatible with authenticator apps."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def provisioning_uri(secret: str, email: str) -> str:
    label = quote(f"Freyja:{email}", safe="")
    query = urlencode(
        {"secret": secret, "issuer": "Freyja", "algorithm": "SHA1", "digits": 6, "period": 30}
    )
    return f"otpauth://totp/{label}?{query}"


def qr_code_data_url(secret: str, email: str) -> str:
    """Returns a browser-renderable PNG QR code for authenticator enrollment."""
    image = qrcode.make(provisioning_uri(secret, email))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def code_at(secret: str, timestamp: int | float | None = None) -> str:
    timestamp = time.time() if timestamp is None else timestamp
    counter = int(timestamp // TOTP_INTERVAL)
    padding = "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(f"{secret.upper()}{padding}")
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(value % (10**TOTP_DIGITS)).zfill(TOTP_DIGITS)


def verify_code(secret: str, code: str, timestamp: int | float | None = None) -> bool:
    if not code.isdigit() or len(code) != TOTP_DIGITS:
        return False
    timestamp = time.time() if timestamp is None else timestamp
    return any(
        hmac.compare_digest(code_at(secret, timestamp + offset * TOTP_INTERVAL), code)
        for offset in (-1, 0, 1)
    )


def _fernet() -> Fernet:
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def decrypt_secret(encrypted_secret: str) -> str:
    return _fernet().decrypt(encrypted_secret.encode()).decode()
