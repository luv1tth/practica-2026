"""Тесты клиента настольной программы на реальном локальном сервере."""
import threading

import pytest
from werkzeug.serving import make_server

from app import create_app
from desktop.api_client import ApiError, NotesClient


@pytest.fixture
def api(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "client.sqlite")})
    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield NotesClient(f"http://127.0.0.1:{server.server_port}", timeout=5)
    server.shutdown()


def test_client_crud(api):
    assert api.health() == {"status": "ok"}
    note = api.create_note("Из программы", "текст")
    assert api.get_note(note["id"])["title"] == "Из программы"
    api.update_note(note["id"], "Изменено", "")
    assert api.list_notes(q="Изменено")["total"] == 1
    api.delete_note(note["id"])
    assert api.list_notes()["total"] == 0


def test_client_errors(api):
    with pytest.raises(ApiError, match="400"):
        api.create_note("")
    with pytest.raises(ApiError, match="404"):
        api.get_note(999)


def test_client_no_server():
    with pytest.raises(ApiError, match="Нет связи"):
        NotesClient("http://127.0.0.1:1", timeout=1).health()
