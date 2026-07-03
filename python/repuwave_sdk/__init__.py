"""
Repuwave Python SDK.

Auto-signing HTTP client for AI agents to authenticate
with the Repuwave trust network using Ed25519.

Quickstart:
    from repuwave_sdk import RepuwaveClient, generate_keypair

    private_key, public_key = generate_keypair()
    client = RepuwaveClient(private_key=private_key, uaid="your-agent-uuid")
"""

from repuwave_sdk.client import RepuwaveAsyncClient, RepuwaveClient
from repuwave_sdk.exceptions import InvalidKeyError, RepuwaveError, SigningError
from repuwave_sdk.signer import Ed25519Signer
from repuwave_sdk.service import RepuwaveService

__all__ = [
    "RepuwaveClient",
    "RepuwaveAsyncClient",
    "Ed25519Signer",
    "RepuwaveError",
    "SigningError",
    "InvalidKeyError",
    "generate_keypair",
    "RepuwaveService",
]

__version__ = "0.1.0"


def generate_keypair() -> tuple[str, str]:
    """
    Generate a new Ed25519 keypair.

    Returns:
        Tuple of (private_key_hex, public_key_hex).

    Example:
        >>> private_key, public_key = generate_keypair()
        >>> len(private_key)
        64
        >>> len(public_key)
        64
    """
    return Ed25519Signer.generate_keypair()
