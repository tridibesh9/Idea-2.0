import hashlib
import hmac
import base64
from app.config import get_settings

settings = get_settings()

def get_blind_index(value: str) -> str:
    """Generate a blind index (hash) for searchable encrypted fields like email."""
    if not value:
        return ""
    # Use HMAC-SHA256 for a strong blind index
    salt = settings.BLIND_INDEX_SALT.encode('utf-8')
    # Normalizing value to lower case for case-insensitive emails
    val_encoded = str(value).lower().strip().encode('utf-8')
    h = hmac.new(salt, val_encoded, hashlib.sha256)
    return base64.b64encode(h.digest()).decode('utf-8')

def get_encryption_key() -> str:
    """Returns the base64 encoded Fernet key."""
    # SQLAlchemy-utils StringEncryptedType requires the key to be a string or bytes
    # Fernet keys are 32 bytes base64 encoded.
    return settings.ENCRYPTION_KEY
