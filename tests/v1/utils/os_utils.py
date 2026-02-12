import os
import sys


def path_includes_drive_letter() -> bool:
    return (
        sys.version_info.major >= 3 and sys.version_info.minor >= 13 and os.name == "nt"
    )
