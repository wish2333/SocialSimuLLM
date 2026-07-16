from socialsimullm.frontend.adapters import normalize_agent_states


def test_normalize_agent_states_preserves_list_records() -> None:
    states = [
        {"name": "Alice", "location": "Library"},
        {"name": "Bob", "location": "Cafe"},
    ]

    assert normalize_agent_states(states) == states


def test_normalize_agent_states_converts_legacy_mapping_to_records() -> None:
    states = {
        "Alice": {"location": "Library"},
        "Bob": {"name": "Robert", "location": "Cafe"},
    }

    assert normalize_agent_states(states) == [
        {"name": "Alice", "location": "Library"},
        {"name": "Robert", "location": "Cafe"},
    ]


def test_normalize_agent_states_ignores_invalid_values() -> None:
    assert normalize_agent_states(None) == []
    assert normalize_agent_states("invalid") == []
    assert normalize_agent_states([{"name": "Alice"}, None, "Bob"]) == [
        {"name": "Alice"}
    ]
