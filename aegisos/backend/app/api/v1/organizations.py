"""Organization API endpoints for EvolvixOS."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.organization import Organization, org_members
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationMemberResponse,
    AddMemberRequest,
)
import uuid
from datetime import datetime, UTC

router = APIRouter(prefix="/organizations", tags=["organizations"])


def _slugify(name: str) -> str:
    """Convert a name to a URL-safe slug."""
    return name.lower().strip().replace(" ", "-").replace("/", "-")[:50]


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new organization."""
    slug = _slugify(org_data.name)
    
    # Check slug uniqueness
    existing = db.query(Organization).filter(Organization.slug == slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organization with slug '{slug}' already exists",
        )

    org = Organization(
        id=str(uuid.uuid4()),
        name=org_data.name,
        slug=slug,
        description=org_data.description,
        owner_id=current_user.id,
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    # Add owner as admin member
    db.execute(
        org_members.insert().values(
            id=str(uuid.uuid4()),
            org_id=org.id,
            user_id=current_user.id,
            role="admin",
            joined_at=datetime.now(UTC),
        )
    )
    db.commit()

    return org


@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List organizations the current user belongs to."""
    orgs = (
        db.query(Organization)
        .join(org_members, org_members.c.org_id == Organization.id)
        .filter(org_members.c.user_id == current_user.id)
        .filter(Organization.is_active == True)
        .all()
    )
    return orgs


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get organization details."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    org_data: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an organization (admin only)."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # Check if user is org admin
    membership = db.execute(
        org_members.select().where(
            org_members.c.org_id == org_id,
            org_members.c.user_id == current_user.id,
        )
    ).first()
    
    if not membership or membership.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this organization")

    if org_data.name:
        org.name = org_data.name
        org.slug = _slugify(org_data.name)
    if org_data.description is not None:
        org.description = org_data.description
    org.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(org)
    return org


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Archive an organization (owner only)."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if org.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can archive this organization")

    org.is_active = False
    org.updated_at = datetime.now(UTC)
    db.commit()
    return None


@router.post("/{org_id}/members", response_model=OrganizationMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    org_id: str,
    member_data: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a member to an organization (org admin only)."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # Check if current user is org admin
    membership = db.execute(
        org_members.select().where(
            org_members.c.org_id == org_id,
            org_members.c.user_id == current_user.id,
        )
    ).first()
    if not membership or membership.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to add members")

    # Check if user is already a member
    existing = db.execute(
        org_members.select().where(
            org_members.c.org_id == org_id,
            org_members.c.user_id == member_data.user_id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member")

    # Add member
    result = db.execute(
        org_members.insert().values(
            id=str(uuid.uuid4()),
            org_id=org_id,
            user_id=member_data.user_id,
            role=member_data.role,
            joined_at=datetime.now(UTC),
        )
    )
    db.commit()

    return OrganizationMemberResponse(
        user_id=member_data.user_id,
        role=member_data.role,
        joined_at=datetime.now(UTC),
    )


@router.get("/{org_id}/members", response_model=List[OrganizationMemberResponse])
async def list_members(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List members of an organization."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    members = db.execute(
        org_members.select().where(org_members.c.org_id == org_id)
    ).fetchall()

    return [
        OrganizationMemberResponse(
            user_id=m.user_id,
            role=m.role,
            joined_at=m.joined_at,
        )
        for m in members
    ]


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a member from an organization (org admin only)."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # Check if current user is org admin
    membership = db.execute(
        org_members.select().where(
            org_members.c.org_id == org_id,
            org_members.c.user_id == current_user.id,
        )
    ).first()
    if not membership or membership.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to remove members")

    # Can't remove the owner
    if user_id == org.owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the organization owner")

    db.execute(
        org_members.delete().where(
            org_members.c.org_id == org_id,
            org_members.c.user_id == user_id,
        )
    )
    db.commit()
    return None
