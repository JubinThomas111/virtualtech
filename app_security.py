import hashlib
import secrets

def process_user_credential(password):
    """
    Handles sensitive user credentials. 
    Logic: Generates a salt, hashes the password, and returns the pair.
    """
    # Generate Gemini Test
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

def check_ip_whitelist(client_ip):
    """
    Verifies if the incoming request is from a trusted Broadcom IP range.
    Returns True if allowed, False otherwise.
    """
    trusted_ips = ["10.0.0.1", "192.168.1.1"]
    return client_ip in trusted_ips

def verify_broadcom_employee(email): return email.endswith('@broadcom.com')
