"""CR-1: personas koda pārbaude iesniegumā. Personas kodi ir sintētiski."""

import pytest


def _post(client, payload, personal_code):
    payload["personalCode"] = personal_code
    return client.post("/submissions", json=payload)


def _issues(response):
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    return [d for d in error["details"] if d["field"] == "personalCode"]


@pytest.mark.parametrize(
    "personal_code, stored",
    [
        ("32000000001", "32000000001"),  # AC1
        ("320000-00001", "32000000001"),  # AC2
        (" 32000000001 ", "32000000001"),  # AC3
        ("311299-21233", "31129921233"),  # AC8
    ],
)
def test_valid_personal_code_is_accepted_and_stored_without_hyphen(
    client, valid_payload, personal_code, stored
):
    response = _post(client, valid_payload, personal_code)
    assert response.status_code == 201
    saved = client.get(f"/submissions/{response.json()['id']}").json()
    assert saved["personalCode"] == stored


@pytest.mark.parametrize(
    "personal_code",
    [
        "3200000000",  # AC4: 10 cipari
        "320000000012",  # AC5: 12 cipari
        "32000000O01",  # AC6: burts O
        "3200-0000001",  # AC9: defise nepareizā vietā
        "320000 00001",  # atstarpe vidū
        "٣٢٠٠٠٠٠٠٠٠١",  # ne-ASCII cipari
    ],
)
def test_invalid_personal_code_returns_invalid_format(
    client, valid_payload, personal_code
):
    response = _post(client, valid_payload, personal_code)
    assert _issues(response) == [{"field": "personalCode", "issue": "INVALID_FORMAT"}]


def test_number_instead_of_string_returns_invalid_format(client, valid_payload):
    response = _post(client, valid_payload, 32000000001)
    assert _issues(response) == [{"field": "personalCode", "issue": "INVALID_FORMAT"}]


def test_missing_personal_code_returns_required(client, valid_payload):
    # AC7
    del valid_payload["personalCode"]
    response = client.post("/submissions", json=valid_payload)
    assert _issues(response) == [{"field": "personalCode", "issue": "REQUIRED"}]


@pytest.mark.parametrize("personal_code", ["", "   ", None])
def test_empty_or_null_personal_code_returns_required(
    client, valid_payload, personal_code
):
    response = _post(client, valid_payload, personal_code)
    assert _issues(response) == [{"field": "personalCode", "issue": "REQUIRED"}]


def test_invalid_submission_is_not_stored(client, valid_payload):
    _post(client, valid_payload, "3200000000")
    created = _post(client, valid_payload, "32000000001").json()
    assert created["id"] == "IES-2026-000001"


def test_error_does_not_repeat_personal_code(client, valid_payload):
    response = _post(client, valid_payload, "32000000O01")
    assert "32000000O01" not in response.text


def test_log_does_not_contain_personal_code(client, valid_payload, caplog):
    caplog.set_level("INFO")
    response = _post(client, valid_payload, "320000-00001")
    assert response.status_code == 201
    assert response.json()["id"] in caplog.text
    assert "32000000001" not in caplog.text
    assert "320000-00001" not in caplog.text
