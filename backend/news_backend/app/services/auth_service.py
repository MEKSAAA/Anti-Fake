import hashlib
import secrets

def hash_password(password):
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{password_hash}:{salt}"

def verify_password(stored_hash, provided_password):
    if ':' not in stored_hash:
        return stored_hash == hashlib.sha256(provided_password.encode()).hexdigest()
    
    hash_val, salt = stored_hash.split(':')
    provided_hash = hashlib.sha256((provided_password + salt).encode()).hexdigest()
    return hash_val == provided_hash
