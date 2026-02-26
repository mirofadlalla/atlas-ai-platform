"""
Authentication and authorization routes.

Handles user registration, login, invitation management, and admin approval workflows.
Also handles multi-tenant SaaS registration for new organizations.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.schema.auth_admin import UserCreate, Token, UserLogin
from app.schema.invitation_requests import (
    SendInvitationRequest,
    InvitationResponse,
    ValidateInvitationRequest,
    InvitationDetailsResponse,
    RegisterViaInvitationRequest,
    ResendInvitationRequest,
    PendingInvitationsResponse,
    ResendInvitationResponse
)

from app.core.db import get_db
from app.services.auth_services.auth_service import get_current_user
from app.services.auth_services.auth_admin_service import AuthService
from app.services.invitation_service import InvitationService
from app.repositories.user_repository import UserRepository
from app.controllers.auth_controller import AuthController
from app.core.rate_limitizer import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth"
)


# ==================== Tenant Registration (SaaS) ====================

from app.schema.tenant_schema import TenantRegistrationRequest, TenantRegistrationResponse


@router.post("/tenant/register", response_model=TenantRegistrationResponse)
def register_tenant(request: TenantRegistrationRequest, db: Session = Depends(get_db)):
    from app.services.tenant_registration_service import TenantRegistrationService
    """
    Register a new tenant (SaaS admin registration).
    Creates organization and first admin user.
    
    This endpoint allows new organizations to create their own Atlas AI workspace.
    
    Args:
        request: Tenant and admin registration data
        db: Database session
        
    Returns:
        Tenant ID, admin user token, and access information
        
    Raises:
        HTTPException: If organization or email already exists
    """
    service = TenantRegistrationService(db)
    return service.register_tenant(request)


# ==================== Basic Authentication ====================

@router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new admin user and create tenant.
    
    Args:
        user: User registration data
        db: Database session
        
    Returns:
        Access token for newly registered admin
    """
    return AuthController.register(user, db)


@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and return access token.
    
    Args:
        user: Login credentials
        db: Database session
        
    Returns:
        Access token
    """
    return AuthController.login(user, db)


@router.get("/profile")
def get_my_profile(current_user=Depends(get_current_user)):
    """
    Get current user's profile information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile data
    """
    from app.services.user_profile_service import UserProfileService
    service = UserProfileService()
    return service.get_profile(current_user)


# ==================== Invitation Management ====================

@router.post("/invitations/send")
def send_invitation(
    request: SendInvitationRequest,
    current_user: str = Header(..., alias="current-user"),
    user_role: str = Header(..., alias="user-role"),
    db: Session = Depends(get_db)
):
    """
    Send invitation to a new user (admin only).
    
    Args:
        request: Invitation request with email and tenant
        current_user: Current admin user ID
        user_role: Current user role (must be 'admin')
        db: Database session
        
    Returns:
        Invitation details with token
    """
    import re
    from app.services.user_approval_service import UserApprovalService
    from app.services.invitation_management_service import InvitationManagementService
    
    # Trim whitespace from headers
    current_user = current_user.strip() if current_user else current_user
    user_role = user_role.strip() if user_role else user_role
    
    # Validate that current_user is a UUID, not an email
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    if '@' in current_user or not uuid_pattern.match(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user ID format. Expected UUID, got: {current_user[:50]}. Please log out and log back in."
        )
    
    approval_service = UserApprovalService(db)
    approval_service.authorize_admin(user_role, "send invitation")
    
    invitation_service = InvitationManagementService(db)
    return invitation_service.send_invitation(
        invited_email=request.invited_email,
        invited_by_id=current_user,
        tenant_id=request.tenant_id,
        admin_id=current_user
    )


@router.get("/invitations/validate")
def validate_invitation(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Validate an invitation token and get details.
    
    Args:
        token: Invitation token
        db: Database session
        
    Returns:
        Invitation details if valid
    """
    from app.services.invitation_management_service import InvitationManagementService
    
    service = InvitationManagementService(db)
    return service.validate_invitation(token)


@router.post("/register-via-invitation")
def register_via_invitation(
    request: RegisterViaInvitationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user using an invitation token.
    
    Args:
        request: Registration request with invitation token and password
        db: Database session
        
    Returns:
        Access token for newly registered user
    """
    from app.services.invitation_management_service import InvitationManagementService
    
    service = InvitationManagementService(db)
    return service.register_via_invitation(
        token=request.token,
        name=request.name,
        password=request.password,
        tenant_id=request.tenant_id
    )


@router.get("/invitations/pending")
def get_pending_invitations(
    current_user: str = Header(..., alias="current-user"),
    user_role: str = Header(..., alias="user-role"),
    db: Session = Depends(get_db)
):
    """
    Get all pending invitations sent by current admin.
    
    Args:
        current_user: Current admin user ID
        user_role: Current user role (must be 'admin')
        db: Database session
        
    Returns:
        List of pending invitations
    """
    import re
    from app.services.user_approval_service import UserApprovalService
    from app.services.invitation_management_service import InvitationManagementService
    
    # Trim whitespace from headers
    current_user = current_user.strip() if current_user else current_user
    user_role = user_role.strip() if user_role else user_role
    
    # Validate that current_user is a UUID, not an email
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    if '@' in current_user or not uuid_pattern.match(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user ID format. Expected UUID, got: {current_user[:50]}. Please log out and log back in."
        )
    
    approval_service = UserApprovalService(db)
    approval_service.authorize_admin(user_role, "view invitations")
    
    invitation_service = InvitationManagementService(db)
    return invitation_service.get_pending_invitations(current_user)


@router.post("/invitations/resend")
def resend_invitation(
    request: ResendInvitationRequest,
    current_user: str = Header(..., alias="current-user"),
    user_role: str = Header(..., alias="user-role"),
    db: Session = Depends(get_db)
):
    """
    Resend an invitation (generate new token).
    
    Args:
        request: Request with current invitation token
        current_user: Current admin user ID
        user_role: Current user role (must be 'admin')
        db: Database session
        
    Returns:
        New invitation token
    """
    from app.services.user_approval_service import UserApprovalService
    from app.services.invitation_management_service import InvitationManagementService
    
    approval_service = UserApprovalService(db)
    approval_service.authorize_admin(user_role, "resend invitation")
    
    invitation_service = InvitationManagementService(db)
    return invitation_service.resend_invitation(request.token)


# ==================== Admin Approval Workflow ====================

@router.get("/pending-approvals")
def get_pending_approvals(
    current_user: str = Header(..., alias="current-user"),
    user_role: str = Header(..., alias="user-role"),
    db: Session = Depends(get_db)
):
    """
    Get list of pending user approvals (admin only).
    
    Args:
        current_user: Current admin user ID
        user_role: Current user role (must be 'admin')
        db: Database session
        
    Returns:
        List of pending users awaiting approval
    """
    from app.services.user_approval_service import UserApprovalService
    
    service = UserApprovalService(db)
    service.authorize_admin(user_role, "view pending approvals")
    
    pending_users = service.get_pending_approvals()
    
    return {
        "total": len(pending_users),
        "pending_users": [
            {
                "user_id": u.id,
                "name": u.name,
                "email": u.email,
                "created_at": u.created_at
            }
            for u in pending_users
        ]
    }


@router.post("/approve-user/{user_id}")
def approve_user(
    user_id: str,
    current_user: str = Header(...),
    user_role: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Approve a pending user registration (admin only).
    
    Args:
        user_id: ID of user to approve
        current_user: Current admin user ID
        user_role: Current user role (must be 'admin')
        db: Database session
        
    Returns:
        Updated user status
    """
    from app.services.user_approval_service import UserApprovalService
    
    service = UserApprovalService(db)
    service.authorize_admin(user_role, "approve user")
    
    return service.approve_user(user_id, current_user)


@router.post("/reject-user/{user_id}")
def reject_user(
    user_id: str,
    current_user: str = Header(...),
    user_role: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Reject a pending user registration (admin only).
    
    Args:
        user_id: ID of user to reject
        current_user: Current admin user ID
        user_role: Current user role (must be 'admin')
        db: Database session
        
    Returns:
        Updated user status
    """
    from app.services.user_approval_service import UserApprovalService
    
    service = UserApprovalService(db)
    service.authorize_admin(user_role, "reject user")
    
    return service.reject_user(user_id, current_user)