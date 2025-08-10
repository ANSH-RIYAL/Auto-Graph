from dataclasses import dataclass, field


@dataclass
class Todo:
    title: str
    completed: bool = False
    id: int = field(default=-1)

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title, "completed": self.completed}

