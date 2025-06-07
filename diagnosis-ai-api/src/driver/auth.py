import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException


security = HTTPBearer()

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


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Firebase認証トークンを検証し、ユーザー情報を返す"""
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"認証エラー: {str(e)}")
