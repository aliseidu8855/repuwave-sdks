"""
Repuwave Python SDK — Exceptions.
"""


class RepuwaveError(Exception):
    """Base exception for all Repuwave SDK errors."""
    pass


class SigningError(RepuwaveError):
    """Raised when request signing fails."""
    pass


class InvalidKeyError(RepuwaveError):
    """Raised when a private or public key is malformed."""
    pass
