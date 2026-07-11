"""Authentication endpoints: dev-friendly login that mints a role-scoped JWT.

For the hackathon demo we don't persist real users — any email + any of the four
known roles logs in. This keeps the role-based demo gates (Fan/Volunteer/Ops/Emergency)
reachable without a signup flow. Production would link to the `users` table.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from app.models.schemas import UserRole
from app.gateway.auth import create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    role: UserRole = UserRole.FAN


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """Mint a JWT for the requested role. Demo mode: no password required."""
    token = create_access_token(user_id=req.email, role=req.role)
    return LoginResponse(access_token=token, role=req.role.value, email=req.email)


@router.get("/roles")
async def list_roles():
    """List the four stakeholder roles for the role-picker UI."""
    return {"roles": [r.value for r in UserRole if r != UserRole.ADMIN]}