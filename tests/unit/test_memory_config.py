import json
import sqlite3
from types import SimpleNamespace

from socialsimullm.agents.memory import AgentMemory


def _write_embedding_db(tmp_path) -> None:
    agent_data = tmp_path / "agent_data"
    agent_data.mkdir()
    connection = sqlite3.connect(agent_data / "Alice_memory.db")
    connection.execute(
        """CREATE TABLE action_embeddings (
            action_index INTEGER,
            action_description TEXT,
            action_embedding TEXT
        )"""
    )
    connection.executemany(
        "INSERT INTO action_embeddings VALUES (?, ?, ?)",
        [
            (1, "semantic match", json.dumps([1.0, 0.0])),
            (2, "important memory", json.dumps([0.0, 1.0])),
        ],
    )
    connection.commit()
    connection.close()


def _memory_file(important_thought: int = 9) -> dict:
    return {
        "memory": [
            {
                "agent_name": "Alice",
                "event_type": "action",
                "content": "semantic",
                "summary": "semantic match",
                "importance": 1,
            },
            {
                "agent_name": "Alice",
                "event_type": "thought",
                "content": "important",
                "summary": "important memory",
                "importance": important_thought,
            },
        ]
    }


def test_memory_config_weights_change_semantic_ranking(tmp_path, monkeypatch) -> None:
    _write_embedding_db(tmp_path)
    config = SimpleNamespace(
        similarity_weight=0.0,
        recency_weight=0.0,
        importance_weight=1.0,
        importance_threshold=8,
    )
    memory = AgentMemory(str(tmp_path), [], 10, memory_config=config)
    monkeypatch.setattr(memory, "_embed_action", lambda query: [1.0, 0.0])
    monkeypatch.setattr(memory, "_load_memory_file", lambda name: _memory_file())

    results = memory.recall_semantic("Alice", "query", top_k=2)

    assert [entry.summary for entry in results] == [
        "important memory",
        "semantic match",
    ]


def test_memory_config_threshold_filters_low_importance_thoughts(
    tmp_path, monkeypatch
) -> None:
    _write_embedding_db(tmp_path)
    config = {
        "similarity_weight": 1.0,
        "recency_weight": 0.0,
        "importance_weight": 0.0,
        "importance_threshold": 9,
    }
    memory = AgentMemory(str(tmp_path), [], 10, memory_config=config)
    monkeypatch.setattr(memory, "_embed_action", lambda query: [1.0, 0.0])
    monkeypatch.setattr(
        memory,
        "_load_memory_file",
        lambda name: _memory_file(important_thought=8),
    )

    results = memory.recall_semantic("Alice", "query", top_k=2)

    assert [entry.summary for entry in results] == ["semantic match"]


def test_memory_config_defaults_preserve_existing_scoring() -> None:
    memory = AgentMemory("/tmp/not-used", [], 10)

    assert memory.retrieval_weights == {
        "similarity": 0.5,
        "recency": 0.3,
        "importance": 0.2,
    }
    assert memory.importance_threshold == 7
