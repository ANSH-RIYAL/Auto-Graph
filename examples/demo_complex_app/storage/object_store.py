from typing import Any, Dict, Optional


class ObjectStore:
    def __init__(self) -> None:
        self._blobs: Dict[str, Any] = {}

    def put_object(self, key: str, value: Any) -> None:
        self._blobs[key] = value

    def get_object(self, key: str) -> Optional[Any]:
        return self._blobs.get(key)