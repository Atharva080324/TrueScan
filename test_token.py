from huggingface_hub import HfApi
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
print(f"Testing token: {token[:10]}...")

try:
    api = HfApi()
    user = api.whoami(token=token)
    print(f"✅ Token is VALID!")
    print(f"Logged in as: {user['name']}")
    print(f"Auth type: {user.get('auth', 'unknown')}")
except Exception as e:
    print(f"❌ Token is INVALID: {e}")
    print("\n🔧 Fix: Go to https://huggingface.co/settings/tokens")
    print("1. Delete the old token")
    print("2. Create a new token with 'Read' permission")
    print("3. Copy the entire token to your .env file")