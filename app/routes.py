"""REST API для заметок: CRUD + поиск + пагинация."""
from flask import Blueprint, abort, jsonify, request

from .db import get_db

bp = Blueprint("notes", __name__, url_prefix="/api/notes")


def row_to_dict(row):
    return dict(row) if row else None


def get_note_or_404(note_id):
    row = get_db().execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if row is None:
        abort(404)
    return row


def validate(data, partial=False):
    """Возвращает (очищенные_данные, ошибка)."""
    if not isinstance(data, dict):
        return None, "Тело запроса должно быть JSON-объектом"
    clean = {}
    if "title" in data or not partial:
        title = data.get("title")
        if not isinstance(title, str) or not title.strip():
            return None, "Поле 'title' обязательно и должно быть непустой строкой"
        if len(title) > 200:
            return None, "Поле 'title' не длиннее 200 символов"
        clean["title"] = title.strip()
    if "content" in data:
        if not isinstance(data["content"], str):
            return None, "Поле 'content' должно быть строкой"
        clean["content"] = data["content"]
    if partial and not clean:
        return None, "Нет полей для обновления"
    return clean, None


@bp.get("")
def list_notes():
    q = request.args.get("q", "").strip()
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("per_page", 10)), 1), 100)
    except ValueError:
        return jsonify(error="page и per_page должны быть числами"), 400

    where, params = "", []
    if q:
        where = "WHERE title LIKE ? OR content LIKE ?"
        params = [f"%{q}%", f"%{q}%"]

    db = get_db()
    total = db.execute(f"SELECT COUNT(*) FROM notes {where}", params).fetchone()[0]
    rows = db.execute(
        f"SELECT * FROM notes {where} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [per_page, (page - 1) * per_page],
    ).fetchall()
    return jsonify(
        items=[row_to_dict(r) for r in rows],
        page=page,
        per_page=per_page,
        total=total,
    )


@bp.get("/<int:note_id>")
def get_note(note_id):
    return jsonify(row_to_dict(get_note_or_404(note_id)))


@bp.post("")
def create_note():
    data, err = validate(request.get_json(silent=True))
    if err:
        return jsonify(error=err), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO notes (title, content) VALUES (?, ?)",
        (data["title"], data.get("content", "")),
    )
    db.commit()
    return jsonify(row_to_dict(get_note_or_404(cur.lastrowid))), 201


@bp.route("/<int:note_id>", methods=["PUT", "PATCH"])
def update_note(note_id):
    get_note_or_404(note_id)
    data, err = validate(request.get_json(silent=True), partial=request.method == "PATCH")
    if err:
        return jsonify(error=err), 400
    if request.method == "PUT":
        data.setdefault("content", "")
    sets = ", ".join(f"{k} = ?" for k in data)
    db = get_db()
    db.execute(
        f"UPDATE notes SET {sets}, updated_at = datetime('now') WHERE id = ?",
        [*data.values(), note_id],
    )
    db.commit()
    return jsonify(row_to_dict(get_note_or_404(note_id)))


@bp.delete("/<int:note_id>")
def delete_note(note_id):
    get_note_or_404(note_id)
    db = get_db()
    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    return "", 204
