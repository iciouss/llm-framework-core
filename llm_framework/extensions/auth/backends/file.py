import json
import pathlib

from .memory import MemoryPolicyBackend


class FilePolicyBackend(MemoryPolicyBackend):
    "RBAC + per-user ACL policy loaded from a JSON file; extends MemoryPolicyBackend with disk persistence."

    def __init__(self, path: str | pathlib.Path):
        """
        Args:
            path: Path to a JSON policy file with `roles` and `users` top-level keys.
        """
        self._path = pathlib.Path(path)
        super().__init__(self._read())

    def _read(self) -> dict:
        return json.loads(self._path.read_text(encoding="utf-8"))

    def reload(self):
        "Re-read the policy file from disk — call when the file changes at runtime."
        self._policy = self._read()
