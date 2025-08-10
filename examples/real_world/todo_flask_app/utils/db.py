from typing import Dict, List

from models.todo import Todo


class InMemoryDB:
    """Tiny in-memory storage to create import/call relationships."""

    def __init__(self) -> None:
        self._items: Dict[int, Todo] = {}
        self._next_id: int = 1

    def add(self, todo: Todo) -> None:
        todo.id = self._next_id
        self._items[self._next_id] = todo
        self._next_id += 1

    def list(self) -> List[Todo]:
        return list(self._items.values())

    def get(self, todo_id: int) -> Todo:
        return self._items[todo_id]

    def update(self, todo: Todo) -> None:
        self._items[todo.id] = todo

