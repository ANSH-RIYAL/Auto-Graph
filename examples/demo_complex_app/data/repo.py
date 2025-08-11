from typing import List, Dict


class Repo:
    def __init__(self) -> None:
        self._rows: List[Dict] = []
        self._next_id = 1

    def list(self) -> List[Dict]:
        return list(self._rows)

    def create(self, row: Dict) -> Dict:
        row = dict(row)
        row["id"] = self._next_id
        self._next_id += 1
        self._rows.append(row)
        return row