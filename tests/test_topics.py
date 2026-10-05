"""CR-0: tēma PARKS un tēmu saraksts GET /topics."""


def test_topics_list_matches_contract(client):
    # AC1 un AC4: precīzs saraksts, esošie kodi un nosaukumi nemainās, OTHER beigās
    response = client.get("/topics")
    assert response.status_code == 200
    assert response.json() == [
        {"code": "ROADS", "name": "Ceļi un ielas"},
        {"code": "WASTE", "name": "Atkritumi"},
        {"code": "PLANNING", "name": "Teritorijas plānošana"},
        {"code": "PARKS", "name": "Parki un skvēri"},
        {"code": "OTHER", "name": "Cits"},
    ]


def test_submission_with_parks_topic_returns_201(client, valid_payload):
    # AC2
    valid_payload["topic"] = "PARKS"
    response = client.post("/submissions", json=valid_payload)
    assert response.status_code == 201
    stored = client.get(f"/submissions/{response.json()['id']}")
    assert stored.json()["topic"] == "PARKS"


def test_submission_with_unknown_topic_returns_validation_error(client, valid_payload):
    # AC3
    valid_payload["topic"] = "ZOO"
    response = client.post("/submissions", json=valid_payload)
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert {"field": "topic", "issue": "INVALID_FORMAT"} in error["details"]
