import json
from types import SimpleNamespace

from socialsimullm.utils import config as runtime_config
from socialsimullm.utils import text_generation
from socialsimullm.utils.logger import StructuredLogger


def _response(content: str, *, prompt: int, completion: int):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=prompt + completion,
        ),
    )


class _Completions:
    def __init__(self, outcomes: list) -> None:
        self.outcomes = outcomes

    def create(self, **kwargs):
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class _Client:
    def __init__(self, outcomes: list, embedding_response=None) -> None:
        self.chat = SimpleNamespace(completions=_Completions(outcomes))
        self.embeddings = SimpleNamespace(
            create=lambda **kwargs: embedding_response
        )


def test_text_call_metadata_contains_usage_but_not_prompt_or_key(monkeypatch) -> None:
    client = _Client([_response("hello", prompt=7, completion=2)])
    monkeypatch.setattr(text_generation, "OpenAI", lambda **kwargs: client)
    monkeypatch.setattr(text_generation, "time_sleep", lambda sec=0.1: None)
    monkeypatch.setattr(runtime_config, "openai_api_key", "sk-private-value")
    text_generation.clear_model_call_metadata()

    result = text_generation.GPT_request(
        "secret system prompt",
        "secret user prompt",
        {"model": "test-model"},
    )

    assert result == "hello"
    records = text_generation.get_model_call_metadata()
    assert records == [
        {
            "call_type": "completion",
            "model": "test-model",
            "retry_count": 0,
            "fallback_used": False,
            "token_usage": {
                "prompt_tokens": 7,
                "completion_tokens": 2,
                "total_tokens": 9,
            },
        }
    ]
    serialized = json.dumps(records)
    assert "secret user prompt" not in serialized
    assert "secret system prompt" not in serialized
    assert "sk-private-value" not in serialized


def test_json_call_metadata_reports_retry_without_fallback(monkeypatch) -> None:
    client = _Client(
        [
            RuntimeError("temporary failure"),
            _response('{"plan": "continue"}', prompt=8, completion=3),
        ]
    )
    monkeypatch.setattr(text_generation, "OpenAI", lambda **kwargs: client)
    monkeypatch.setattr(text_generation, "time_sleep", lambda sec=0.1: None)
    monkeypatch.setattr(runtime_config.DefaultModel, "completion", "deepseek-v4-flash")
    monkeypatch.setattr(runtime_config, "json_mode_enabled", True)
    text_generation.clear_model_call_metadata()

    result = text_generation.GPT_request_json(
        "system",
        "prompt",
        required_keys=["plan"],
        fallback={"plan": "fallback"},
    )

    assert result == {"plan": "continue"}
    record = text_generation.get_model_call_metadata()[0]
    assert record["model"] == "deepseek-v4-flash"
    assert record["retry_count"] == 1
    assert record["fallback_used"] is False
    assert record["token_usage"]["total_tokens"] == 11


def test_json_call_metadata_reports_plain_mode_fallback(monkeypatch) -> None:
    client = _Client(
        [
            _response("not json", prompt=2, completion=1),
            _response("still not json", prompt=3, completion=1),
            _response("plain but invalid", prompt=4, completion=2),
        ]
    )
    monkeypatch.setattr(text_generation, "OpenAI", lambda **kwargs: client)
    monkeypatch.setattr(text_generation, "time_sleep", lambda sec=0.1: None)
    monkeypatch.setattr(runtime_config.DefaultModel, "completion", "deepseek-v4-flash")
    monkeypatch.setattr(runtime_config, "json_mode_enabled", True)
    text_generation.clear_model_call_metadata()

    result = text_generation.GPT_request_json(
        "system",
        "prompt",
        required_keys=["rating"],
        fallback={"rating": 5},
    )

    assert result == {"rating": 5}
    record = text_generation.get_model_call_metadata()[0]
    assert record["retry_count"] == 2
    assert record["fallback_used"] is True
    assert record["token_usage"]["total_tokens"] == 13


def test_non_deep_json_fallback_is_recorded_once(monkeypatch) -> None:
    client = _Client([_response("not json", prompt=5, completion=1)])
    monkeypatch.setattr(text_generation, "OpenAI", lambda **kwargs: client)
    monkeypatch.setattr(text_generation, "time_sleep", lambda sec=0.1: None)
    monkeypatch.setattr(runtime_config.DefaultModel, "completion", "gpt-test")
    monkeypatch.setattr(runtime_config, "json_mode_enabled", True)
    text_generation.clear_model_call_metadata()

    result = text_generation.GPT_request_json(
        "system",
        "prompt",
        required_keys=["rating"],
        fallback={"rating": 5},
    )

    assert result == {"rating": 5}
    assert text_generation.get_model_call_metadata() == [
        {
            "call_type": "completion_json",
            "model": "gpt-test",
            "retry_count": 0,
            "fallback_used": True,
            "token_usage": {
                "prompt_tokens": 5,
                "completion_tokens": 1,
                "total_tokens": 6,
            },
        }
    ]


def test_embedding_metadata_can_be_drained_to_a_persistence_sink(monkeypatch) -> None:
    embedding_response = SimpleNamespace(
        data=[SimpleNamespace(embedding=[0.1, 0.2])],
        usage=SimpleNamespace(prompt_tokens=4, total_tokens=4),
    )
    client = _Client([], embedding_response=embedding_response)
    captured: list[dict] = []
    monkeypatch.setattr(text_generation, "OpenAI", lambda **kwargs: client)
    monkeypatch.setattr(runtime_config, "embedding_api_key", "embedding-secret")
    text_generation.clear_model_call_metadata()
    text_generation.set_model_call_metadata_sink(captured.append)

    try:
        assert text_generation.get_embedding("private input", "embedding-model") == [
            0.1,
            0.2,
        ]
        drained = text_generation.drain_model_call_metadata()
    finally:
        text_generation.set_model_call_metadata_sink(None)

    assert drained == captured
    assert drained[0] == {
        "call_type": "embedding",
        "model": "embedding-model",
        "retry_count": 0,
        "fallback_used": False,
        "token_usage": {
            "prompt_tokens": 4,
            "completion_tokens": 0,
            "total_tokens": 4,
        },
    }
    assert text_generation.get_model_call_metadata() == []
    serialized = json.dumps(drained)
    assert "private input" not in serialized
    assert "embedding-secret" not in serialized


def test_structured_logger_persists_only_safe_model_metadata(tmp_path) -> None:
    logger = StructuredLogger(str(tmp_path))
    logger.log_model_call(
        {
            "call_type": "completion",
            "model": "test-model",
            "retry_count": 1,
            "fallback_used": True,
            "token_usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
            "prompt": "must not persist",
            "api_key": "sk-secret",
        }
    )

    persisted = json.loads((tmp_path / "model_calls.jsonl").read_text(encoding="utf-8"))
    assert persisted["model"] == "test-model"
    assert persisted["token_usage"]["total_tokens"] == 5
    serialized = json.dumps(persisted)
    assert "must not persist" not in serialized
    assert "sk-secret" not in serialized
