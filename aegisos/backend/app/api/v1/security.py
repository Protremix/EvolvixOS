"""API for Security Features — Phase 27."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.two_factor_auth import get_2fa_service
from app.services.transaction_security import get_tx_security_service
from app.services.security_scanner import get_security_scanner

router = APIRouter(prefix="/security", tags=["security"])


# --- 2FA Endpoints ---

class Enable2FARequest(BaseModel):
    secret: str
    verification_code: str

class Verify2FARequest(BaseModel):
    code: str

@router.post("/2fa/setup")
async def setup_2fa(current_user: User = Depends(get_current_active_user)):
    """Generate TOTP secret for 2FA setup."""
    service = get_2fa_service()
    secret = service.generate_secret()
    otpauth_url = service.get_otpauth_url(secret, current_user.email)
    return {"secret": secret, "otpauth_url": otpauth_url}

@router.post("/2fa/enable")
async def enable_2fa(req: Enable2FARequest, current_user: User = Depends(get_current_active_user)):
    """Enable 2FA after verifying the TOTP code."""
    service = get_2fa_service()
    if service.verify_code(req.secret, req.verification_code):
        config = service.enable(current_user.id, req.secret)
        return {"enabled": True, "backup_codes": config.backup_codes}
    return {"enabled": False, "error": "Invalid verification code"}

@router.post("/2fa/verify")
async def verify_2fa(req: Verify2FARequest, current_user: User = Depends(get_current_active_user)):
    """Verify a 2FA code."""
    service = get_2fa_service()
    return {"valid": service.verify(current_user.id, req.code)}

@router.post("/2fa/disable")
async def disable_2fa(current_user: User = Depends(get_current_active_user)):
    """Disable 2FA."""
    service = get_2fa_service()
    return {"disabled": service.disable(current_user.id)}

@router.get("/2fa/status")
async def get_2fa_status(current_user: User = Depends(get_current_active_user)):
    """Check if 2FA is enabled."""
    service = get_2fa_service()
    return {"enabled": service.is_enabled(current_user.id)}

@router.post("/2fa/backup-codes")
async def regenerate_backup_codes(current_user: User = Depends(get_current_active_user)):
    """Generate new backup codes."""
    service = get_2fa_service()
    codes = service.regenerate_backup_codes(current_user.id)
    return {"backup_codes": codes}


# --- Transaction Security Endpoints ---

class CreateTransactionRequest(BaseModel):
    sender: str
    recipient: str
    amount: str
    private_key: str

@router.post("/transactions/sign")
async def sign_transaction(req: CreateTransactionRequest, current_user: User = Depends(get_current_active_user)):
    """Create and sign a transaction."""
    service = get_tx_security_service()
    tx = service.create_transaction(req.sender, req.recipient, req.amount, req.private_key)
    return tx.to_dict()

@router.get("/transactions/stats")
async def get_tx_stats(current_user: User = Depends(get_current_active_user)):
    """Get transaction statistics."""
    service = get_tx_security_service()
    return service.get_stats()


@router.get("/transactions/{tx_id}")
async def get_transaction(tx_id: str, current_user: User = Depends(get_current_active_user)):
    """Get a signed transaction."""
    service = get_tx_security_service()
    tx = service.get_transaction(tx_id)
    return tx.to_dict() if tx else {"error": "not found"}

@router.get("/transactions/history/{address}")
async def get_tx_history(address: str, current_user: User = Depends(get_current_active_user)):
    """Get transaction history for an address."""
    service = get_tx_security_service()
    return [tx.to_dict() for tx in service.get_history(address)]

@router.get("/transactions/nonce/{address}")
async def get_nonce(address: str, current_user: User = Depends(get_current_active_user)):
    """Get current nonce for an address."""
    service = get_tx_security_service()
    return {"nonce": service.get_nonce(address)}



# --- Security Scanner Endpoints ---

@router.post("/scan")
async def run_scan(current_user: User = Depends(get_current_active_user)):
    """Run a security scan on the codebase."""
    scanner = get_security_scanner()
    findings = scanner.scan_directory("app")
    return {"findings": len(findings), "results": [f.to_dict() for f in findings[:50]]}

@router.get("/scan/results")
async def get_scan_results(severity: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    """Get security scan results."""
    scanner = get_security_scanner()
    return [f.to_dict() for f in scanner.get_findings(severity)]

@router.get("/scan/summary")
async def get_scan_summary(current_user: User = Depends(get_current_active_user)):
    """Get security scan summary."""
    scanner = get_security_scanner()
    return scanner.get_summary()
