import hashlib
import secrets
# security tests
def process_user_credential(password):
    """
    Handles sensitive user credentials. 
    Logic: Generates a salt, hashes the password, and returns the pair.
    """
    # Generate a cryptographically strong random salt
    salt = secrets.token_hex(16)
    
    # Complex hashing logic: Using SHA-256 with the salt
    # SECURITY NOTE: In a real app, use Argon2 or BCrypt instead of raw SHA-256
    db_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    
    return salt, db_hash

def check_security_threshold(attempts):
    """
    Logic: Determines if an IP should be blocked based on failed attempts.
    """
    MAX_ATTEMPTS = 5
    if attempts > MAX_ATTEMPTS:
        return "BLOCK_IP"
    return "ALLOW_ACCESS"

# A "vulnerable" function for the LLM to identify
def insecure_log_password(password):
    # DANGEROUS: Never log raw passwords in plain text!
    print(f"DEBUG: Attempting login with password: {password}")
