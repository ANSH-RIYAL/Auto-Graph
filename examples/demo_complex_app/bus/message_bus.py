from typing import Any, Dict, List


class MessageBus:
    def __init__(self) -> None:
        self._topics: Dict[str, List[Any]] = {}

    def publish(self, topic: str, message: Any) -> None:
        self._topics.setdefault(topic, []).append(message)

    def history(self, topic: str) -> List[Any]:
        return list(self._topics.get(topic, []))