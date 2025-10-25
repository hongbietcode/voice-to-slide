"""Rate limiting middleware for API requests."""

import os
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from api.models.rate_limit import RateLimit


class RateLimiter:
    """
    Rate limiter for upload requests.

    Enforces a limit on the number of uploads per IP address within a time window.
    """

    def __init__(
        self,
        max_uploads: int = None,
        window_minutes: int = None
    ):
        """
        Initialize rate limiter.

        Args:
            max_uploads: Maximum uploads allowed per window (default: from env or 3)
            window_minutes: Time window in minutes (default: from env or 60)
        """
        self.max_uploads = max_uploads or int(os.getenv("RATE_LIMIT_MAX_UPLOADS", "3"))
        self.window_minutes = window_minutes or int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "60"))

    def get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request.

        Checks X-Forwarded-For and X-Real-IP headers for proxied requests.

        Args:
            request: FastAPI request object

        Returns:
            Client IP address as string
        """
        # Check X-Forwarded-For header (for proxied requests)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP (client IP)
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    def check_rate_limit(self, ip_address: str, db: Session) -> dict:
        """
        Check if IP address has exceeded rate limit.

        Args:
            ip_address: Client IP address
            db: Database session

        Returns:
            dict with:
                - allowed (bool): Whether request is allowed
                - remaining (int): Remaining uploads in current window
                - reset_at (datetime): When the window resets
                - retry_after (int): Seconds until next allowed request (if blocked)

        Raises:
            HTTPException: If rate limit exceeded
        """
        now = datetime.utcnow()

        # Get or create rate limit record
        rate_limit = db.query(RateLimit).filter(RateLimit.ip_address == ip_address).first()

        if not rate_limit:
            # First upload from this IP
            rate_limit = RateLimit(
                ip_address=ip_address,
                upload_count=1,
                last_upload_at=now,
                window_start=now
            )
            db.add(rate_limit)
            db.commit()

            return {
                "allowed": True,
                "remaining": self.max_uploads - 1,
                "reset_at": now + timedelta(minutes=self.window_minutes),
                "retry_after": 0
            }

        # Check if window has expired
        window_end = rate_limit.window_start + timedelta(minutes=self.window_minutes)

        if now >= window_end:
            # Window expired, reset counter
            rate_limit.upload_count = 1
            rate_limit.window_start = now
            rate_limit.last_upload_at = now
            db.commit()

            return {
                "allowed": True,
                "remaining": self.max_uploads - 1,
                "reset_at": now + timedelta(minutes=self.window_minutes),
                "retry_after": 0
            }

        # Window still active, check limit
        if rate_limit.upload_count >= self.max_uploads:
            # Rate limit exceeded
            retry_after = int((window_end - now).total_seconds())

            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"You can only upload {self.max_uploads} file(s) per {self.window_minutes} minutes",
                    "retry_after": retry_after,
                    "reset_at": window_end.isoformat()
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.max_uploads),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(window_end.timestamp()))
                }
            )

        # Increment counter
        rate_limit.upload_count += 1
        rate_limit.last_upload_at = now
        db.commit()

        return {
            "allowed": True,
            "remaining": self.max_uploads - rate_limit.upload_count,
            "reset_at": window_end,
            "retry_after": 0
        }

    async def __call__(self, request: Request, db: Session):
        """
        Middleware call for dependency injection.

        Args:
            request: FastAPI request
            db: Database session

        Returns:
            Rate limit check result
        """
        ip_address = self.get_client_ip(request)
        return self.check_rate_limit(ip_address, db)


# Default rate limiter instance
rate_limiter = RateLimiter()
