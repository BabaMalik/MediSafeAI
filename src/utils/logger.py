"""
Logging Configuration Module
Provides structured logging with JSON support, file rotation, and audit logging
"""

import logging
import logging.handlers
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

from src.config.settings import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        # Add custom attributes
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                          'extra_fields', 'message']:
                log_data[key] = value

        return json.dumps(log_data)


class StandardFormatter(logging.Formatter):
    """
    Standard formatter with color support for console output
    """

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }

    def __init__(self, use_colors: bool = True):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with optional colors"""
        if self.use_colors:
            levelname = record.levelname
            color = self.COLORS.get(levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{levelname}{self.COLORS['RESET']}"

        return super().format(record)


class AuditLogger:
    """
    Specialized logger for HIPAA compliance audit logging
    """

    def __init__(self, log_file: str):
        self.logger = logging.getLogger('medisafe.audit')
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        # Ensure audit log directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        # File handler for audit logs
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT
        )
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def log_access(self, user: str, resource: str, action: str, **kwargs):
        """Log data access event"""
        self.logger.info(
            f"Data access: {action} on {resource}",
            extra={
                'event_type': 'data_access',
                'user': user,
                'resource': resource,
                'action': action,
                **kwargs
            }
        )

    def log_privacy_operation(self, operation: str, epsilon: float, delta: float, **kwargs):
        """Log differential privacy operation"""
        self.logger.info(
            f"Privacy operation: {operation}",
            extra={
                'event_type': 'privacy_operation',
                'operation': operation,
                'epsilon': epsilon,
                'delta': delta,
                **kwargs
            }
        )

    def log_data_generation(self, generator_type: str, num_records: int, **kwargs):
        """Log data generation event"""
        self.logger.info(
            f"Data generation: {generator_type}",
            extra={
                'event_type': 'data_generation',
                'generator_type': generator_type,
                'num_records': num_records,
                **kwargs
            }
        )

    def log_export(self, export_format: str, destination: str, **kwargs):
        """Log data export event"""
        self.logger.info(
            f"Data export to {destination}",
            extra={
                'event_type': 'data_export',
                'export_format': export_format,
                'destination': destination,
                **kwargs
            }
        )

    def log_user_action(self, user_id: str, action: str, details: Dict[str, Any] = None, **kwargs):
        """Log user authentication and authorization events"""
        self.logger.info(
            f"User action: {action}",
            extra={
                'event_type': 'user_action',
                'user_id': user_id,
                'action': action,
                'details': details or {},
                **kwargs
            }
        )


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> None:
    """
    Set up application logging

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        log_format: Format type ('json' or 'standard')
    """
    log_level = log_level or settings.LOG_LEVEL
    log_file = log_file or settings.LOG_FILE
    log_format = log_format or settings.LOG_FORMAT

    # Ensure log directory exists
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if log_format == 'json':
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(StandardFormatter(use_colors=True))

    root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(JSONFormatter() if log_format == 'json' else StandardFormatter(use_colors=False))
        root_logger.addHandler(file_handler)

    # Set up library loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

    root_logger.info(
        f"Logging initialized: level={log_level}, format={log_format}, file={log_file}"
    )


@lru_cache()
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


@lru_cache()
def get_audit_logger() -> AuditLogger:
    """
    Get the audit logger instance

    Returns:
        AuditLogger instance
    """
    if not settings.AUDIT_LOG_ENABLED:
        # Return a no-op logger if audit logging is disabled
        class NoOpAuditLogger:
            def log_access(self, *args, **kwargs): pass
            def log_privacy_operation(self, *args, **kwargs): pass
            def log_data_generation(self, *args, **kwargs): pass
            def log_export(self, *args, **kwargs): pass
            def log_user_action(self, *args, **kwargs): pass

        return NoOpAuditLogger()

    return AuditLogger(settings.AUDIT_LOG_FILE)


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class
    """

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__module__)
        return self._logger

    def log_with_context(self, level: str, message: str, **context):
        """Log message with additional context"""
        extra = {'extra_fields': context}
        getattr(self.logger, level.lower())(message, extra=extra)


# Initialize logging on module import if in application mode
if settings.APP_ENV != "testing":
    setup_logging()
