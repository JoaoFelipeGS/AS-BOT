import json
import os

FILE = "selected_imoveis.json"


def load():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add(url):
    data = load()
    if url not in data:
        data.append(url)
        save(data)


def remove(url):
    data = load()
    if url in data:
        data.remove(url)
        save(data)


def clear():
    save([])