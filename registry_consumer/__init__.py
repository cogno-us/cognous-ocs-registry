"""S04 bounded registry overlay consumer (non-authorizing, unqualified, not wired to Runtime).

See docs/s04-implementation.md. One fixed profile: a trusted host verifies a pinned selection manifest, authenticates one
record against it, validates it with the frozen S03 validator, and narrows a caller-constructed LocalExecutionPolicy by
set intersection on exactly three fields. Any refusal leaves the caller policy exactly as constructed.
"""
from .consumer import (
    CONSUMER_REASON_CODES,
    EFFECTIVE_FIELDS,
    MANIFEST_TYPE,
    MANIFEST_VERSION,
    OverlayResult,
    TrustConfig,
    apply_registry_overlay,
)

__all__ = [
    "CONSUMER_REASON_CODES",
    "EFFECTIVE_FIELDS",
    "MANIFEST_TYPE",
    "MANIFEST_VERSION",
    "OverlayResult",
    "TrustConfig",
    "apply_registry_overlay",
]
