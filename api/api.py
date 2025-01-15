# api.py
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import uuid
import os

from database import get_db, Token, TokenUsage, init_db

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
API_KEY_NAME = "X-Admin-Key"
API_KEY = os.getenv("ADMIN_API_KEY")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_admin_key(api_key: str = Security(api_key_header)):
    if not api_key or api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin API key"
        )
    return api_key

# Models
class TokenCreate(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    roles: List[str]
    profile: dict

class TokenVerification(BaseModel):
    token: str

class TokenResponse(BaseModel):
    token: str
    user_id: str
    username: str
    roles: List[str]

# Token verification endpoint for GPT-Trainer
@app.post("/verify-token")
async def verify_token(
    verification: TokenVerification,
    db: Session = Depends(get_db)
):
    token_record = db.query(Token).filter(
        Token.token == verification.token,
        Token.is_active == True
    ).first()
    
    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Record usage
    usage = TokenUsage(
        id=str(uuid.uuid4()),
        token=verification.token,
        endpoint="/verify-token",
        success=True,
        request_data=verification.dict()
    )
    db.add(usage)
    
    # Update last used timestamp
    token_record.last_used = datetime.utcnow()
    db.commit()
    
    return {
        "userId": token_record.user_id,
        "userName": token_record.username,
        "roles": token_record.roles,
        "profile": token_record.profile
    }

# Admin endpoints for token management
@app.post("/admin/tokens")
async def create_token(
    token_data: TokenCreate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    # Generate a secure token
    new_token = str(uuid.uuid4())
    
    token_record = Token(
        token=new_token,
        user_id=token_data.user_id,
        username=token_data.username,
        email=token_data.email,
        roles=token_data.roles,
        profile=token_data.profile
    )
    
    db.add(token_record)
    db.commit()
    
    return {"token": new_token}

@app.delete("/admin/tokens/{token}")
async def deactivate_token(
    token: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    token_record = db.query(Token).filter(Token.token == token).first()
    if not token_record:
        raise HTTPException(status_code=404, detail="Token not found")
    
    token_record.is_active = False
    db.commit()
    
    return {"status": "success"}

@app.get("/admin/tokens/usage")
async def get_token_usage(
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    usage = db.query(TokenUsage).order_by(TokenUsage.timestamp.desc()).limit(100).all()
    return usage

# Startup event
@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)