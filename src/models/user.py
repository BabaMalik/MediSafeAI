"""
User Model for Authentication
Manages user accounts and permissions for MediSafeAI API
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

from src.models.base import Base


class UserRole(enum.Enum):
    """User role types"""
    ADMIN = "admin"
    RESEARCHER = "researcher"
    DATA_SCIENTIST = "data_scientist"
    VIEWER = "viewer"


class User(Base):
    """User account model"""
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Privacy budget tracking
    privacy_budget_used = Column(String, default='0.0', nullable=False)

    def __init__(self, username, email, password, role=UserRole.VIEWER, **kwargs):
        """Initialize user with hashed password"""
        import uuid
        self.id = str(uuid.uuid4())
        self.username = username
        self.email = email
        self.set_password(password)
        self.role = role
        for key, value in kwargs.items():
            setattr(self, key, value)

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value if isinstance(self.role, UserRole) else self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'privacy_budget_used': self.privacy_budget_used
        }

    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', role='{self.role}')>"
