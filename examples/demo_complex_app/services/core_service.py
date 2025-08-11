from typing import List, Dict
from data.repo import Repo
from cache.memory_cache import MemoryCache
from storage.object_store import ObjectStore
from search.inverted_index import InvertedIndex
from bus.message_bus import MessageBus
from queueing.task_queue import TaskQueue
from scheduling.jobs import schedule_daily_compaction
from integrations.external_api import ExternalAPI
from integrations.llm_service import LLMService


class CoreService:
    def __init__(self) -> None:
        self.repo = Repo()
        self.cache = MemoryCache()
        self.store = ObjectStore()
        self.search_index = InvertedIndex()
        self.bus = MessageBus()
        self.queue = TaskQueue()
        self.external = ExternalAPI()
        self.llm = LLMService()
        schedule_daily_compaction(self.search_index)

    def list_items(self) -> List[Dict]:
        cached = self.cache.get("items")
        if cached is not None:
            return cached
        items = self.repo.list()
        self.cache.set("items", items, ttl=30)
        return items

    def create_item(self, name: str) -> Dict:
        item = self.repo.create({"name": name})
        self.search_index.add_document(str(item["id"]), name)
        self.store.put_object(f"items/{item['id']}.json", item)
        self.bus.publish("items.created", item)
        self.queue.enqueue("post_create", {"id": item["id"]})
        try:
            _ = self.external.notify_create(item)
        except Exception:
            pass
        # generate short description using LLM (optional)
        try:
            desc = self.llm.summarize(name)
            item["summary"] = desc
        except Exception:
            item["summary"] = ""
        self.cache.delete("items")
        return item

    def search(self, query: str) -> List[Dict]:
        ids = self.search_index.search(query)
        results = []
        for i in ids:
            obj = self.store.get_object(f"items/{i}.json")
            if obj:
                results.append(obj)
        return results