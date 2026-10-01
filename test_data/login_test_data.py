"""
No real credentials here - the valid username/password come from .env.
"""

# ----- Expected messages
USERNAME_REQUIRED = "Username is required."
PASSWORD_REQUIRED = "Password is required."
INVALID_CREDENTIALS = "These credentials do not match our records."
TOO_MANY_ATTEMPTS = "Too Many Attempts"
PASSWORD_TOO_SHORT = "Password must be at least 8 characters."

# ----- Negative test data (TC_LOGIN_006, 008, 009) -----
INVALID_USERNAME = "test"
INVALID_PASSWORD = "test_password"
SHORT_PASSWORD = "123"
CASE_SENSITIVE_PASSWORD = "$USHAN@GENIU$2026#"  

# Text of the Sign in button while the request is processing (TC_LOGIN_002)
LOADING_BUTTON_TEXT = "Please wait"
