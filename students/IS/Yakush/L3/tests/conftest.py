import json
import math
import re
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import config
from app.api.main import app
from app.db import vector_store
from app.errors import IndexEmpty
from app.logic import chunking, embeddings, llm

import seed_db


class FakeTokenizer:
    def __call__(self, text, **kwargs):
        return {"offset_mapping": [match.span() for match in re.finditer(r"\S+", text)]}


def fake_embed(texts):
    vectors = []
    for text in texts:
        vector = [0.0] * 64
        for word in re.findall(r"\w+", text.lower()):
            vector[sum(word.encode()) % 64] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        vectors.append([value / norm for value in vector])
    return vectors


class FakeStore:
    def __init__(self):
        self.points = []

    def recreate(self, vectors, payloads):
        self.points = list(zip(vectors, payloads))
        return len(self.points)

    def search(self, vector, limit):
        if not self.points:
            raise IndexEmpty("База знаний пуста, сначала вызовите /index")
        scored = sorted(
            ((sum(a * b for a, b in zip(vector, point)), payload) for point, payload in self.points),
            key=lambda item: item[0],
            reverse=True,
        )
        return [{"score": score, **payload} for score, payload in scored[:limit]]


class FakeLLM:
    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []

    def __call__(self, messages, tools=None):
        self.requests.append({"messages": [dict(message) for message in messages], "tools": tools})
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def text_reply(content):
    return SimpleNamespace(content=content, tool_calls=None)


def tool_reply(name, arguments, call_id="call_1"):
    call = SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments, ensure_ascii=False)),
    )
    return SimpleNamespace(content="", tool_calls=[call])


@pytest.fixture
def env(tmp_path, monkeypatch):
    store = FakeStore()
    db_path = tmp_path / "network.db"
    seed_db.seed(db_path)
    monkeypatch.setattr(config, "SQL_PATH", db_path)
    monkeypatch.setattr(config, "TEMP_DIR", tmp_path / "temp")
    monkeypatch.setattr(embeddings, "embed_texts", fake_embed)
    monkeypatch.setattr(vector_store, "get_store", lambda: store)
    monkeypatch.setattr(chunking, "get_tokenizer", lambda: FakeTokenizer())
    return SimpleNamespace(store=store, temp=tmp_path / "temp", db=db_path)


@pytest.fixture
def client(env):
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def use_llm(monkeypatch):
    def install(*replies):
        fake = FakeLLM(replies)
        monkeypatch.setattr(llm, "chat", fake)
        return fake

    return install
