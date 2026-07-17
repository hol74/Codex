from __future__ import annotations

import os
import platform


def nofollow_platform_qualification() -> dict[str, object]:
    native = hasattr(os, "O_NOFOLLOW")
    return {
        "platform": platform.system(),
        "oNoFollowAvailable": native,
        "symlinkPrecheckEnabled": True,
        "lstatFstatDeviceInodeCheckEnabled": True,
        "regularFileDescriptorCheckEnabled": True,
        "qualificationMode": "native-o-nofollow-plus-descriptor-identity" if native else "descriptor-identity-fallback",
        "failClosedOnIdentityChange": True,
    }
