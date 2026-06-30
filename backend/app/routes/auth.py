import uuid
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from app.database import get_db
from app.models.agent import Agent
from app.config import get_settings

router = APIRouter()
settings = get_settings()

class LoginRequest(BaseModel):
    email: EmailStr

class LoginResponse(BaseModel):
    token: str
    id: uuid.UUID
    name: str
    email: str
    role: str
    department: str | None

class AgentListItem(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    department: str | None

    class Config:
        from_attributes = True

@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.email == payload.email))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent email not found. Please contact support.")

    # Create JWT token
    expire = datetime.utcnow() + timedelta(minutes=1440) # 24 hours
    token_data = {
        "sub": str(agent.id),
        "email": agent.email,
        "role": agent.role,
        "department": agent.department,
        "exp": expire
    }
    token = jwt.encode(token_data, settings.JWT_SECRET, algorithm="HS256")

    return LoginResponse(
        token=token,
        id=agent.id,
        name=agent.name,
        email=agent.email,
        role=agent.role,
        department=agent.department
    )

@router.get("/agents", response_model=List[AgentListItem])
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).order_by(Agent.name))
    return result.scalars().all()
