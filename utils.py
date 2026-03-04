import hashlib
def hash_password(password: str) -> str:
    """將密碼進行 SHA256 編碼"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()