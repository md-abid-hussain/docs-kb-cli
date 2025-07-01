import os
import requests
from rich.console import Console
from rich.prompt import Prompt

console = Console()

def get_or_request_github_token() -> str:
    """Get GitHub token from environment or request from user."""
    token = os.getenv("GITHUB_TOKEN")
    
    if token:
        # Validate existing token
        if validate_github_token(token):
            return token
        else:
            console.print("⚠️ Existing GitHub token is invalid", style="yellow")
    
    console.print("🔑 GitHub token required for API access", style="blue")
    token = Prompt.ask("Enter GitHub token", password=True)
    
    if not token or not token.strip():
        console.print("❌ No token provided", style="red")
        return None
    
    token = token.strip()
    
    # Validate the new token
    if not validate_github_token(token):
        console.print("❌ Invalid GitHub token", style="red")
        return None
    
    # Set for current session only
    os.environ["GITHUB_TOKEN"] = token
    console.print("✅ Token set for current session", style="green")
    
    return token

def validate_github_token(token: str) -> bool:
    """Validate GitHub token by making a test API call."""
    try:
        headers = {"Authorization": f"token {token}"}
        response = requests.get(
            "https://api.github.com/user", 
            headers=headers, 
            timeout=10
        )
        return response.status_code == 200
    except Exception:
        return False