from .memory import MemoryStore
from .mcp import MCPClient, MCPManager, MCPContext, MCPServer
from .auth import (
    AuthContext,
    AuthGate,
    AuthProvider,
    FilePolicyBackend,
    MemoryPolicyBackend,
    PolicyBackend,
    StaticAuthProvider,
)

__all__ = [
    "MemoryStore",
    "AuthContext",
    "AuthGate",
    "AuthProvider",
    "FilePolicyBackend",
    "MemoryPolicyBackend",
    "OIDCAuthProvider",
    "PolicyBackend",
    "StaticAuthProvider",
    "MCPClient",
    "MCPManager",
    "MCPContext",
    "MCPServer",
    "RAGStore",
]

try:
    from .auth import OIDCAuthProvider
except (ImportError, AttributeError):

    class OIDCAuthProvider:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "OIDCAuthProvider requires [oidc] extra: pip install .[oidc]"
            )


try:
    from .rag import RAGStore
except ImportError:

    class RAGStore:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "RAGStore requires extras. Install with: pip install .[rag]"
            )
