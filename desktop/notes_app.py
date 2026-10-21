"""Настольная программа «Заметки» — клиент для Notes API.

Запуск:  python desktop/notes_app.py
Адрес сервера можно поменять прямо в окне программы.
"""
import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk

try:
    from .api_client import ApiError, NotesClient
except ImportError:
    from api_client import ApiError, NotesClient

DEFAULT_URL = os.environ.get("NOTES_API_URL", "https://notes-api-8iec.onrender.com")
PER_PAGE = 20


class NotesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Заметки — клиент Notes API")
        self.geometry("860x540")
        self.minsize(640, 400)

        self.client = NotesClient(DEFAULT_URL)
        self.notes = []
        self.current_id = None
        self.page = 1
        self.total = 0
        self._search_job = None

        self._build_ui()
        self.refresh(quiet=True)
    #интерфейс
    def _build_ui(self):
        pad = {"padx": 6, "pady": 4}

        top = ttk.Frame(self)
        top.pack(fill="x", **pad)
        ttk.Label(top, text="Сервер:").pack(side="left")
        self.url_var = tk.StringVar(value=DEFAULT_URL)
        ttk.Entry(top, textvariable=self.url_var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(top, text="Подключиться", command=self.connect).pack(side="left")

        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, **pad)

        # левая панель: поиск и список
        left = ttk.Frame(body)
        body.add(left, weight=1)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._schedule_search())
        search = ttk.Entry(left, textvariable=self.search_var)
        search.pack(fill="x")
        ttk.Label(left, text="Поиск по заголовку и тексту", foreground="gray").pack(anchor="w")

        self.listbox = tk.Listbox(left, activestyle="none", exportselection=False)
        self.listbox.pack(fill="both", expand=True, pady=4)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        pager = ttk.Frame(left)
        pager.pack(fill="x")
        self.prev_btn = ttk.Button(pager, text="←", width=3, command=lambda: self.change_page(-1))
        self.prev_btn.pack(side="left")
        self.page_label = ttk.Label(pager, text="")
        self.page_label.pack(side="left", expand=True)
        self.next_btn = ttk.Button(pager, text="→", width=3, command=lambda: self.change_page(1))
        self.next_btn.pack(side="right")

        # правая панель: редактор
        right = ttk.Frame(body)
        body.add(right, weight=2)
        ttk.Label(right, text="Заголовок").pack(anchor="w")
        self.title_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.title_var).pack(fill="x")
        ttk.Label(right, text="Текст").pack(anchor="w", pady=(6, 0))
        self.content = tk.Text(right, wrap="word", height=10, undo=True)
        self.content.pack(fill="both", expand=True)

        btns = ttk.Frame(right)
        btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Новая", command=self.new_note).pack(side="left")
        ttk.Button(btns, text="Сохранить", command=self.save_note).pack(side="left", padx=6)
        ttk.Button(btns, text="Удалить", command=self.delete_note).pack(side="left")

        self.status = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w").pack(fill="x", side="bottom")

        self.bind("<Control-s>", lambda _: self.save_note())
        self.bind("<Control-n>", lambda _: self.new_note())

    #фоновые запросы, чтобы окно не зависало
    def run_async(self, func, on_success, message="Загрузка...", quiet=False):
        self.status.set(message)
        self.config(cursor="watch")

        def worker():
            try:
                result = func()
            except ApiError as e:
                self.after(0, self._on_error, str(e), quiet)
            else:
                self.after(0, self._on_done, on_success, result)

        threading.Thread(target=worker, daemon=True).start()

    def _on_done(self, callback, result):
        self.config(cursor="")
        self.status.set(f"Подключено к {self.client.base_url}")
        callback(result)

    def _on_error(self, message, quiet=False):
        self.config(cursor="")
        self.status.set(message + " — проверьте адрес и нажмите «Подключиться»")
        if not quiet:
            messagebox.showerror("Ошибка", message)

    #действия 
    def connect(self):
        self.client = NotesClient(self.url_var.get().strip())
        self.page = 1
        self.refresh()

    def _schedule_search(self):
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(400, self._do_search)

    def _do_search(self):
        self.page = 1
        self.refresh()

    def refresh(self, select_id=None, quiet=False):
        q = self.search_var.get().strip()
        page = self.page
        self.run_async(lambda: self.client.list_notes(q, page, PER_PAGE),
                       lambda data: self._show_list(data, select_id), quiet=quiet)

    def _show_list(self, data, select_id=None):
        self.notes = data["items"]
        self.total = data["total"]
        self.listbox.delete(0, "end")
        for n in self.notes:
            self.listbox.insert("end", n["title"])
        pages = max(1, -(-self.total // PER_PAGE))
        self.page_label.config(text=f"Стр. {self.page} из {pages} · всего {self.total}")
        self.prev_btn.state(["!disabled"] if self.page > 1 else ["disabled"])
        self.next_btn.state(["!disabled"] if self.page < pages else ["disabled"])
        if select_id is not None:
            for i, n in enumerate(self.notes):
                if n["id"] == select_id:
                    self.listbox.selection_set(i)
                    self.listbox.see(i)

    def change_page(self, delta):
        self.page += delta
        self.refresh()

    def on_select(self, _event):
        sel = self.listbox.curselection()
        if not sel:
            return
        note = self.notes[sel[0]]
        self.current_id = note["id"]
        self.title_var.set(note["title"])
        self.content.delete("1.0", "end")
        self.content.insert("1.0", note["content"])

    def new_note(self):
        self.current_id = None
        self.listbox.selection_clear(0, "end")
        self.title_var.set("")
        self.content.delete("1.0", "end")

    def save_note(self):
        title = self.title_var.get().strip()
        content = self.content.get("1.0", "end-1c")
        if not title:
            messagebox.showwarning("Заметки", "Введите заголовок")
            return
        if self.current_id is None:
            func = lambda: self.client.create_note(title, content)
        else:
            note_id = self.current_id
            func = lambda: self.client.update_note(note_id, title, content)

        def done(note):
            self.current_id = note["id"]
            self.refresh(select_id=note["id"])

        self.run_async(func, done, "Сохранение...")

    def delete_note(self):
        if self.current_id is None:
            return
        if not messagebox.askyesno("Заметки", "Удалить заметку?"):
            return
        note_id = self.current_id
        self.run_async(lambda: self.client.delete_note(note_id),
                       lambda _: (self.new_note(), self.refresh()), "Удаление...")


if __name__ == "__main__":
    NotesApp().mainloop()
