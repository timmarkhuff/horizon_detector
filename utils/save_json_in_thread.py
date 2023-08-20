import json
from threading import Thread

def save_json_in_thread(filepath: str, data: dict) -> None:
    def thread():
        with open(filepath, "w") as f:
            json.dump(data, f)

    Thread(target=thread).start()