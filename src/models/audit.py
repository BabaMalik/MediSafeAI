"""
Audit and Compliance Models
Database models for tracking data access, privacy operations, and compliance
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from sqlalchemy.sql import func

from src.models.base import Base


class AuditLog(Base):
    """
    Audit log for HIPAA compliance
    Tracks all data access and modifications
    """
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Event information
    event_type = Column(String(50), nullable=False, index=True)
    event_action = Column(String(100), nullable=False)
    event_description = Column(Text, nullable=True)

    # User/system information
    user_id = Column(String(100), nullable=True)
    system_component = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Resource information
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True, index=True)

    # Additional context
    event_metadata = Column(JSON, nullable=True)

    # Status
    status = Column(String(20), nullable=False, default='success')
    error_message = Column(Text, nullable=True)

    # Timestamp
    timestamp = Column(DateTime, server_default=func.now(), index=True)

    def __repr__(self):
        return f"<AuditLog {self.event_type}: {self.event_action} at {self.timestamp}>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'event_action': self.event_action,
            'event_description': self.event_description,
            'user_id': self.user_id,
            'system_component': self.system_component,
            'ip_address': self.ip_address,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'event_metadata': self.event_metadata,
            'status': self.status,
            'error_message': self.error_message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }


class PrivacyOperation(Base):
    """
    Track differential privacy operations
    Maintains privacy budget accounting
    """
    __tablename__ = 'privacy_operations'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Privacy parameters
    epsilon = Column(Float, nullable=False)
    delta = Column(Float, nullable=False)
    mechanism = Column(String(20), nullable=False)  # laplace, gaussian, etc.

    # Operation details
    operation_type = Column(String(50), nullable=False)  # privatize, aggregate, etc.
    data_source = Column(String(255), nullable=False)
    columns_affected = Column(JSON, nullable=True)
    num_records = Column(Integer, nullable=True)

    # Privacy budget tracking
    cumulative_epsilon = Column(Float, nullable=True)
    cumulative_delta = Column(Float, nullable=True)

    # Results
    output_file = Column(String(255), nullable=True)
    statistics = Column(JSON, nullable=True)

    # Metadata
    user_id = Column(String(100), nullable=True)
    session_id = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)

    def __repr__(self):
        return f"<PrivacyOperation ε={self.epsilon} δ={self.delta} at {self.created_at}>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'epsilon': self.epsilon,
            'delta': self.delta,
            'mechanism': self.mechanism,
            'operation_type': self.operation_type,
            'data_source': self.data_source,
            'columns_affected': self.columns_affected,
            'num_records': self.num_records,
            'cumulative_epsilon': self.cumulative_epsilon,
            'cumulative_delta': self.cumulative_delta,
            'output_file': self.output_file,
            'statistics': self.statistics,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
