"""
Authentication and authorization routes.

Handles user registration, login, invitation management, and admin approval workflows.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

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
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "tenant_id": current_user.tenant_id,
        "role": current_user.role,
        "approval_status": current_user.approval_status
    }


# ==================== Invitation Management ====================

@router.post("/invitations/send")
def send_invitation(
    request: SendInvitationRequest,
    current_user: str = Header(...),
    user_role: str = Header(...),
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
        
    Raises:
        HTTPException: If user is not admin
    """
    # Verify admin role
    if user_role != "admin":
        logger.warning(f"Unauthorized invitation attempt by {current_user}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can send invitations"
        )
    
    # Apply rate limiting
    rate_limit(
        user_id=current_user,
        role="admin",
        endpoint="/auth/invitations/send"
    )
    
    try:
        invitation_service = InvitationService(db)
        
        invitation = invitation_service.send_invitation(
            invited_email=request.invited_email,
            invited_by_id=current_user,
            tenant_id=request.tenant_id
        )
        
        logger.info(
            f"Invitation sent to {request.invited_email} by admin {current_user}"
        )
        
        return {
            "invitation_id": invitation.invitation_id,
            "invited_email": invitation.invited_email,
            "token": invitation.token,
            "status": invitation.status,
            "created_at": invitation.created_at,
            "expires_at": invitation.expires_at
        }
        
    except ValueError as e:
        logger.error(f"Error sending invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error sending invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send invitation"
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
        
    Raises:
        HTTPException: If invitation is invalid or expired
    """
    try:
        invitation_service = InvitationService(db)
        details = invitation_service.get_invitation_details(token)
        
        if not details:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation token"
            )
        
        return details
        
    except Exception as e:
        logger.error(f"Error validating invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate invitation"
        )


@router.post("/register-via-invitation")
def register_via_invitation(
    request: RegisterViaInvitationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user using an invitation token.
    
    After registration, user status will be 'pending' if admin approval is required,
    or 'approved' if immediate approval is configured.
    
    Args:
        request: Registration request with invitation token and password
        db: Database session
        
    Returns:
        Access token for newly registered user
        
    Raises:
        HTTPException: If invitation is invalid or registration fails
    """
    try:
        invitation_service = InvitationService(db)
        
        # Validate invitation
        details = invitation_service.get_invitation_details(request.token)
        if not details:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation token"
            )
        
        # Hash password
        from app.services.hash_service import password_hash
        password_hash_obj = password_hash(request.password)
        
        # Register user
        user = invitation_service.accept_invitation_and_register(
            token=request.token,
            name=request.name,
            password_hash=password_hash_obj,
            tenant_id=request.tenant_id
        )
        
        # Generate access token
        from app.services.token_service import create_access_token
        access_token = create_access_token({
            "sub": user.email,
            "tenant_id": user.tenant_id,
            "role": user.role,
            "approval_status": user.approval_status
        })
        
        logger.info(f"User registered via invitation: {user.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "approval_status": user.approval_status,
            "message": "Please await admin approval" if user.approval_status == "pending" else "Registration successful"
        }
        
    except ValueError as e:
        logger.error(f"Invalid invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error registering via invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.get("/invitations/pending")
def get_pending_invitations(
    current_user: str = Header(...),
    user_role: str = Header(...),
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
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view invitations"
        )
    
    try:
        invitation_service = InvitationService(db)
        invitations = invitation_service.get_pending_invitations_for_admin(current_user)
        
        return {
            "total": len(invitations),
            "invitations": [
                {
                    "invitation_id": inv.invitation_id,
                    "invited_email": inv.invited_email,
                    "status": inv.status,
                    "created_at": inv.created_at,
                    "expires_at": inv.expires_at
                }
                for inv in invitations
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving pending invitations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invitations"
        )


@router.post("/invitations/resend")
def resend_invitation(
    request: ResendInvitationRequest,
    current_user: str = Header(...),
    user_role: str = Header(...),
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
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can resend invitations"
        )
    
    try:
        invitation_service = InvitationService(db)
        new_token = invitation_service.resend_invitation(request.token)
        
        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot resend this invitation"
            )
        
        return {
            "success": True,
            "new_token": new_token,
            "message": "Invitation resent successfully"
        }
    except Exception as e:
        logger.error(f"Error resending invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend invitation"
        )


# ==================== Admin Approval Workflow ====================

@router.get("/pending-approvals")
def get_pending_approvals(
    current_user: str = Header(...),
    user_role: str = Header(...),
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
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view pending approvals"
        )
    
    try:
        user_repo = UserRepository(db)
        # Get all pending users (this assumes a method exists or we query directly)
        from app.models.user import Users
        pending_users = db.query(Users).filter(
            Users.approval_status == "pending"
        ).all()
        
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
    except Exception as e:
        logger.error(f"Error retrieving pending approvals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending approvals"
        )


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
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can approve users"
        )
    
    try:
        from app.models.user import Users
        from datetime import datetime
        
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.approval_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User already {user.approval_status}"
            )
        
        user.approval_status = "approved"
        user.approved_by = current_user
        user.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        logger.info(f"User {user.email} approved by admin {current_user}")
        
        return {
            "user_id": user.id,
            "email": user.email,
            "approval_status": user.approval_status,
            "approved_at": user.approved_at
        }
    except Exception as e:
        logger.error(f"Error approving user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve user"
        )


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
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can reject users"
        )
    
    try:
        from app.models.user import Users
        from datetime import datetime
        
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.approval_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject user with status: {user.approval_status}"
            )
        
        user.approval_status = "rejected"
        user.approved_by = current_user
        user.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        logger.info(f"User {user.email} rejected by admin {current_user}")
        
        return {
            "user_id": user.id,
            "email": user.email,
            "approval_status": user.approval_status,
            "rejected_at": user.approved_at
        }
    except Exception as e:
        logger.error(f"Error rejecting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject user"
        )