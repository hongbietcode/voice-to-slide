"""Rate limit model for tracking user uploads."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, TIMESTAMP
from api.database import Base


class RateLimit(Base):
    """
    Rate limit model for tracking upload requests by IP.

    Tracks the number of uploads and the timestamp of the last upload
    to enforce rate limiting policies.
    """
    __tablename__ = "rate_limits"

    # IP address as primary key
    ip_address = Column(String(45), primary_key=True)  # Supports IPv6

    # Upload tracking
    upload_count = Column(Integer, default=0, nullable=False)
    last_upload_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Window tracking
    window_start = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Additional metadata
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<RateLimit(ip={self.ip_address}, count={self.upload_count}, last={self.last_upload_at})>"
