"""
Pydantic schemas for invitation-related requests and responses.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class SendInvitationRequest(BaseModel):
    """Request to send an invitation to a user."""
    invited_email: EmailStr
    tenant_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "invited_email": "user@example.com",
                "tenant_id": "tenant-123"
            }
        }


class InvitationResponse(BaseModel):
    """Response containing invitation details."""
    invitation_id: str
    invited_email: str
    status: str
    created_at: datetime
    expires_at: datetime
    token: Optional[str] = None  # Only included when first created
    
    class Config:
        from_attributes = True


class ValidateInvitationRequest(BaseModel):
    """Request to validate an invitation token."""
    token: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
            }
        }


class InvitationDetailsResponse(BaseModel):
    """Response with invitation details."""
    invited_email: str
    tenant_id: str
    created_at: str
    expires_at: str
    is_expired: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "invited_email": "user@example.com",
                "tenant_id": "tenant-123",
                "created_at": "2024-02-24T10:00:00",
                "expires_at": "2024-03-02T10:00:00",
                "is_expired": False
            }
        }


class RegisterViaInvitationRequest(BaseModel):
    """Request to register a new user via invitation."""
    token: str
    name: str
    password: str
    tenant_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "name": "John Doe",
                "password": "secure_password_123",
                "tenant_id": "tenant-123"
            }
        }


class ResendInvitationRequest(BaseModel):
    """Request to resend an invitation."""
    token: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
            }
        }


class PendingInvitationsResponse(BaseModel):
    """Response containing list of pending invitations."""
    total: int
    invitations: list[InvitationResponse]


class ResendInvitationResponse(BaseModel):
    """Response after resending invitation."""
    success: bool
    message: str
    new_token: Optional[str] = None
