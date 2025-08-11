from typing import List, Dict


class TaskQueue:
    def __init__(self) -> None:
        self._q: List[Dict] = []

    def enqueue(self, task: str, payload: Dict) -> None:
        self._q.append({"task": task, "payload": payload})

    def drain(self) -> List[Dict]:
        items = list(self._q)
        self._q.clear()
        return items