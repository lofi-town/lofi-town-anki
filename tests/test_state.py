from addon.state import DEFAULT_STATE, normalize_state


def test_uses_defaults_for_invalid_state() -> None:
    assert normalize_state(None) == DEFAULT_STATE
    assert normalize_state({"area": "top", "width": "wide"}) == DEFAULT_STATE


def test_normalizes_saved_state() -> None:
    state = normalize_state(
        {
            "visible": False,
            "area": "left",
            "width": 2000,
            "floating": True,
            "geometry": "abc",
            "zoom_factor": 0.1,
        }
    )
    assert state == {
        "visible": False,
        "area": "left",
        "width": 1200,
        "floating": True,
        "geometry": "abc",
        "zoom_factor": 0.5,
    }
