import os
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from fastapi.security import HTTPAuthorizationCredentials

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    # Get the path to the firebase credentials file
    cred_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "firebase-adminsdk.json",
    )

    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized with credentials from:", cred_path)
    else:
        # For production, use default credentials
        firebase_admin.initialize_app()
        print("Firebase initialized with default credentials")


async def get_firebase_user(credentials: HTTPAuthorizationCredentials):
    """Firebase認証トークンを検証し、ユーザー情報を返す"""
    try:
        token = credentials.credentials
        print(f"Received token: {token}..." if len(token) > 50 else token)
        # Add clock skew tolerance of 10 seconds
        decoded_token = firebase_auth.verify_id_token(token, clock_skew_seconds=10)
        print(
            f"Successfully decoded token for user: {decoded_token.get('user_id', 'unknown')}"
        )
        return decoded_token
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        print(f"Token type: {type(token)}")
        print(f"Token length: {len(token) if token else 'None'}")
        raise ValueError(
            f"Invalid authentication token. Please provide a valid Firebase ID token. {str(e)}",
        )
