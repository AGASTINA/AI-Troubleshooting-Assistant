import json
from types import SimpleNamespace

import pytest

import ai_assistant
import repairs
from app import app


@pytest.fixture()
def client(monkeypatch):
    app.config.update(TESTING=True)
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)
    with app.test_client() as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
    assert response.get_json()["engine"] == "local_rules"


def test_uses_valid_hosted_model_response(client, monkeypatch):
    monkeypatch.setenv("AI_API_KEY", "test-secret")
    monkeypatch.setenv("AI_MODEL", "test-model")
    diagnosis = {
        "category": "network",
        "title": "Connection trouble",
        "answer": "Try these checks.",
        "steps": ["Check Wi-Fi is on.", "Reconnect to the network."],
        "follow_up": "Do other devices connect?",
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({
                "choices": [{"message": {"content": json.dumps(diagnosis)}}]
            }).encode("utf-8")

    def fake_urlopen(provider_request, timeout):
        assert provider_request.get_header("Authorization") == "Bearer test-secret"
        assert timeout == 25
        return FakeResponse()

    monkeypatch.setattr(ai_assistant.urllib.request, "urlopen", fake_urlopen)
    response = client.post("/api/chat", json={"message": "My Wi-Fi is not working"})

    assert response.status_code == 200
    assert response.get_json()["engine"] == "hosted_model"
    assert response.get_json()["title"] == "Connection trouble"


def test_invalid_hosted_response_falls_back_to_rules(client, monkeypatch):
    monkeypatch.setenv("AI_API_KEY", "test-secret")
    monkeypatch.setenv("AI_MODEL", "test-model")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({
                "choices": [{"message": {"content": "not JSON"}}]
            }).encode("utf-8")

    monkeypatch.setattr(ai_assistant.urllib.request, "urlopen", lambda *_args, **_kwargs: FakeResponse())
    response = client.post("/api/chat", json={"message": "My Wi-Fi is not working"})

    assert response.status_code == 200
    assert response.get_json()["engine"] == "local_rules"
    assert response.get_json()["category"] == "network"
    assert "using local rules" in response.get_json()["model_notice"]


@pytest.mark.parametrize(
    ("message", "expected_category"),
    [
        ("My Wi-Fi is not working", "network"),
        ("I cannot log in to my account", "login"),
        ("My laptop is very slow", "performance"),
        ("The application keeps crashing", "application"),
        ("My printer is not printing", "printer"),
        ("How do I bake a cake?", "unknown"),
    ],
)
def test_chat_categories(client, message, expected_category):
    response = client.post("/api/chat", json={"message": message})
    assert response.status_code == 200
    data = response.get_json()
    assert data["category"] == expected_category
    assert data["engine"] == "local_rules"
    assert isinstance(data["steps"], list)
    assert len(data["steps"]) > 0
    assert data["title"]


def test_rejects_empty_message(client):
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_rejects_missing_message(client):
    response = client.post("/api/chat", json={})
    assert response.status_code == 400


def test_rejects_non_json(client):
    response = client.post("/api/chat", data="message=hello",
                           content_type="application/x-www-form-urlencoded")
    assert response.status_code == 415


def test_rejects_too_long_message(client):
    response = client.post("/api/chat", json={"message": "x" * 1001})
    assert response.status_code == 400


def test_normalizes_case_and_whitespace(client):
    response = client.post("/api/chat", json={"message": "  WIFI   IS NOT WORKING "})
    assert response.status_code == 200
    assert response.get_json()["category"] == "network"


def test_network_response_offers_allowlisted_windows_repair(client, monkeypatch):
    monkeypatch.setattr(repairs.platform, "system", lambda: "Windows")
    response = client.post("/api/chat", json={"message": "My Wi-Fi is not working"})
    assert response.status_code == 200
    assert response.get_json()["repairs"] == [
        {
            "id": "flush_dns_cache",
            "title": "Flush the DNS cache",
            "description": "Clears cached name lookups. It does not change network settings or delete files.",
        }
    ]


def test_repair_requires_explicit_confirmation(client):
    response = client.post("/api/repairs/flush_dns_cache", json={})
    assert response.status_code == 400
    assert "confirmation" in response.get_json()["error"]


def test_unknown_repair_is_rejected(client):
    response = client.post("/api/repairs/run-anything", json={"confirmed": True})
    assert response.status_code == 404


def test_confirmed_dns_repair_runs_only_fixed_command(client, monkeypatch):
    monkeypatch.setattr(repairs.platform, "system", lambda: "Windows")
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(repairs.subprocess, "run", fake_run)
    response = client.post("/api/repairs/flush_dns_cache", json={"confirmed": True})

    assert response.status_code == 200
    assert response.get_json()["status"] == "completed"
    assert calls == [
        (["ipconfig", "/flushdns"], {
            "capture_output": True,
            "text": True,
            "timeout": 20,
            "check": False,
            "shell": False,
        })
    ]


def test_confirmed_store_repair_launches_only_fixed_utility(client, monkeypatch, tmp_path):
    monkeypatch.setattr(repairs.platform, "system", lambda: "Windows")
    monkeypatch.setenv("WINDIR", str(tmp_path))
    store_reset = tmp_path / "System32" / "wsreset.exe"
    store_reset.parent.mkdir()
    store_reset.touch()
    calls = []

    def fake_popen(command, **kwargs):
        calls.append((command, kwargs))

    monkeypatch.setattr(repairs.subprocess, "Popen", fake_popen)
    response = client.post("/api/repairs/reset_store_cache", json={"confirmed": True})

    assert response.status_code == 200
    assert response.get_json()["status"] == "started"
    assert calls == [([str(store_reset)], {"close_fds": True})]
