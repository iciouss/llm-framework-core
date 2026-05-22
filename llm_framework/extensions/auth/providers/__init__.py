from .static import StaticAuthProvider

__all__ = ["StaticAuthProvider"]

try:
    from .oidc import OIDCAuthProvider

    __all__ = ["OIDCAuthProvider", "StaticAuthProvider"]
except ImportError:
    pass
