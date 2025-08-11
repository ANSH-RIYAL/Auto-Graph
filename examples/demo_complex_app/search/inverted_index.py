from typing import Dict, List
import re


class InvertedIndex:
    def __init__(self) -> None:
        self._index: Dict[str, List[str]] = {}

    def add_document(self, doc_id: str, text: str) -> None:
        for token in self._tokenize(text):
            self._index.setdefault(token, []).append(doc_id)

    def search(self, query: str) -> List[str]:
        tokens = self._tokenize(query)
        if not tokens:
            return []
        results = None
        for t in tokens:
            ids = set(self._index.get(t, []))
            results = ids if results is None else results & ids
        return list(results or [])

    def _tokenize(self, text: str) -> List[str]:
        return [t for t in re.findall(r"[a-zA-Z0-9]+", text.lower()) if t]