"""Клиент REST API сервиса заметок (только стандартная библиотека Python)."""
import json
import urllib.error
import urllib.parse
import urllib.request


class ApiError(Exception):
    """Ошибка при обращении к серверу."""


class NotesClient:
    def __init__(self, base_url, timeout=60):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout  # бесплатный Render «просыпается» до минуты

    def _request(self, method, path, data=None):
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(self.base_url + path, data=body, method=method)
        if body is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read()).get("error", str(e))
            except Exception:
                msg = str(e)
            raise ApiError(f"Ошибка {e.code}: {msg}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ApiError(f"Нет связи с сервером {self.base_url}") from e

    def health(self):
        return self._request("GET", "/health")

    def list_notes(self, q="", page=1, per_page=20):
        query = urllib.parse.urlencode({"q": q, "page": page, "per_page": per_page})
        return self._request("GET", f"/api/notes?{query}")

    def get_note(self, note_id):
        return self._request("GET", f"/api/notes/{note_id}")

    def create_note(self, title, content=""):
        return self._request("POST", "/api/notes", {"title": title, "content": content})

    def update_note(self, note_id, title, content):
        return self._request("PUT", f"/api/notes/{note_id}", {"title": title, "content": content})

    def delete_note(self, note_id):
        self._request("DELETE", f"/api/notes/{note_id}")
