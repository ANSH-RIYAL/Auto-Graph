import schedule
from search.inverted_index import InvertedIndex


def schedule_daily_compaction(index: InvertedIndex) -> None:
    # In real life this would compact/rotate indexes; here it's a no-op placeholder
    def _task():
        return True

    schedule.every().day.at("03:00").do(_task)