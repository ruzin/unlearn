from models.user import User

def send_welcome_email(user: User) -> bool:
    """Send a welcome email to a new user."""
    return send_email(user.email, "Welcome!", f"Hello {user.name}")

def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email via SMTP."""
    return True
