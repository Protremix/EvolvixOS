
"""
Signed URL File Storage — Self-Hosted.
Provides time-limited signed download URLs for private files.
Also adds CDN-style public/private file separation.
"""
import os
import time
import json
import uuid
import hashlib
import hmac
import base64
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

SIGNING_KEY = os.environ.get("FILE_SIGNING_KEY", "evolvixos-file-signing-2026-v1")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/opt/evolvixos/uploads")


class SignedURLManager:
    """Generate and verify time-limited signed URLs for private files."""
    
    @staticmethod
    def generate_signed_url(file_id: str, file_path: str, expires_in: int = 300) -> str:
        """
        Generate a time-limited signed URL for a private file.
        
        Args:
            file_id: File UUID
            file_path: Path to the file on disk
            expires_in: Expiration time in seconds (default: 5 minutes)
            
        Returns:
            Signed URL path like /api/files/{file_id}/signed?token=xxx&expires=123
        """
        expires_at = int(time.time()) + expires_in
        
        # Create signature
        message = f"{file_id}:{expires_at}"
        signature = hmac.new(
            SIGNING_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Base64-encode for URL
        token = base64.urlsafe_b64encode(f"{expires_at}:{signature}".encode()).decode()
        
        return f"/api/files/{file_id}/signed?token={token}"
    
    @staticmethod
    def verify_signed_url(file_id: str, token: str) -> tuple[bool, str]:
        """
        Verify a signed URL token.
        
        Returns:
            (is_valid, error_message)
        """
        try:
            decoded = base64.urlsafe_b64decode(token).decode()
            expires_at_str, signature = decoded.split(":", 1)
            expires_at = int(expires_at_str)
            
            # Check expiration
            if time.time() > expires_at:
                return False, "URL has expired"
            
            # Verify signature
            message = f"{file_id}:{expires_at}"
            expected_signature = hmac.new(
                SIGNING_KEY.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return False, "Invalid signature"
            
            return True, "ok"
            
        except Exception as e:
            return False, f"Invalid token: {str(e)}"
    
    @staticmethod
    async def create_signed_url_from_db(db: AsyncSession, file_id: str, expires_in: int = 300) -> Optional[str]:
        """Create a signed URL for a file stored in the database."""
        result = await db.execute(
            text("SELECT file_path, is_private FROM platform_files WHERE file_id = :id OR file_path LIKE :pattern"),
            {"id": file_id, "pattern": f"{file_id}_%"}
        )
        row = result.fetchone()
        if not row:
            return None
        
        file_path = row[0]
        is_private = row[1] if len(row) > 1 else False
        
        if not is_private:
            # Public files don't need signed URLs
            return f"/api/files/{file_id}"
        
        return SignedURLManager.generate_signed_url(file_id, file_path, expires_in)


class FileStorageManager:
    """Manage file uploads with public/private separation (Self-Hosted)."""
    
    @staticmethod
    async def upload(
        db: AsyncSession,
        filename: str,
        content: bytes,
        content_type: str,
        is_private: bool = False,
        user_id: str = None
    ) -> dict:
        """
        Upload a file to storage.
        
        Args:
            is_private: If True, file requires signed URL for download
            user_id: Owner of the file
            
        Returns:
            dict with file_id, url (public or private uri), size
        """
        file_id = str(uuid.uuid4())
        stored_filename = f"{file_id}_{filename}"
        file_path = os.path.join(UPLOAD_DIR, stored_filename)
        
        # Write to disk
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Store in database
        await db.execute(text("""
            INSERT INTO platform_files (file_id, filename, file_path, content_type, file_size, is_private, created_by)
            VALUES (:fid, :name, :path, :type, :size, :private, :uid)
        """), {
            "fid": file_id, "name": filename, "path": file_path,
            "type": content_type, "size": len(content),
            "private": is_private, "uid": user_id
        })
        await db.commit()
        
        if is_private:
            # Return private URI (requires signed URL to download)
            return {
                "file_id": file_id,
                "file_uri": f"private://{file_id}",
                "is_private": True,
                "size": len(content),
                "filename": filename
            }
        else:
            # Return public URL
            return {
                "file_id": file_id,
                "url": f"/api/files/{file_id}",
                "is_private": False,
                "size": len(content),
                "filename": filename
            }
    
    @staticmethod
    async def download(db: AsyncSession, file_id: str, token: str = None) -> Optional[dict]:
        """
        Download a file. If private, requires a valid signed URL token.
        
        Returns:
            dict with file_path, filename, content_type, or None if not found/unauthorized
        """
        result = await db.execute(
            text("SELECT file_path, filename, content_type, is_private FROM platform_files WHERE file_id = :id OR file_path LIKE :pattern"),
            {"id": file_id, "pattern": f"{file_id}_%"}
        )
        row = result.fetchone()
        if not row:
            return None
        
        file_path, filename, content_type, is_private = row
        
        if is_private:
            # Require signed URL token
            if not token:
                return {"error": "Private file requires signed URL", "status": 403}
            
            is_valid, error = SignedURLManager.verify_signed_url(file_id, token)
            if not is_valid:
                return {"error": error, "status": 403}
        
        return {
            "file_path": file_path,
            "filename": filename,
            "content_type": content_type or "application/octet-stream"
        }
