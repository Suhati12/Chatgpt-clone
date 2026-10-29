
"""
ChatGPT Clone — powered by g4f (free GPT-4 access, no API key needed)
Install deps:  python -m pip install g4f
Run:           python chat_app.py
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import datetime

# ── Try importing g4f ────────────────────────────────────────────
try:
    import g4f
    from g4f.client import Client
    G4F_OK = True
except ImportError:
    G4F_OK = False

# ── Palette (ChatGPT-style dark) ─────────────────────────────────
BG_MAIN     = "#212121"
BG_SIDEBAR  = "#171717"
BG_INPUT    = "#2f2f2f"
BG_USER     = "#2f2f2f"
BG_BOT      = "#212121"
BG_HOVER    = "#2a2a2a"
ACCENT      = "#10a37f"       # ChatGPT green
ACCENT_H    = "#0d8c6d"
TEXT_PRI    = "#ececec"
TEXT_SEC    = "#8e8ea0"
TEXT_USER   = "#ececec"
TEXT_BOT    = "#d1d5db"
BORDER      = "#3a3a3a"
SEND_BG     = "#10a37f"
SEND_FG     = "#ffffff"
DANGER      = "#ef4444"
WHITE       = "#ffffff"

FONT_UI     = ("Segoe UI",    10)
FONT_MSG    = ("Segoe UI",    11)
FONT_CODE   = ("Consolas",    10)
FONT_TITLE  = ("Segoe UI",    13, "bold")
FONT_SMALL  = ("Segoe UI",     8)
FONT_TIME   = ("Segoe UI",     8)


class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ChatGPT")
        self.root.geometry("1100x720")
        self.root.configure(bg=BG_MAIN)
        self.root.resizable(True, True)

        self.history     = []   # [{role, content}]
        self.chats       = []   # list of chat sessions
        self.current_chat= []
        self.typing      = False
        self.model_var   = tk.StringVar(value="gpt-4o-mini")

        self._build_ui()
        self._new_chat()

    # ════════════════════════════════════════════════════════════
    # UI BUILD
    # ════════════════════════════════════════════════════════════
    def _build_ui(self):
        # ── Sidebar ──────────────────────────────────────────────
        self.sidebar = tk.Frame(self.root, bg=BG_SIDEBAR, width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        logo_frame.pack(fill="x", padx=14, pady=(18,10))
        tk.Label(logo_frame, text="⬡", bg=BG_SIDEBAR, fg=ACCENT,
                 font=("Segoe UI",20)).pack(side="left")
        tk.Label(logo_frame, text=" ChatGPT", bg=BG_SIDEBAR, fg=WHITE,
                 font=("Segoe UI",14,"bold")).pack(side="left")

        # New Chat button
        new_btn = tk.Button(self.sidebar,
            text="＋  New chat",
            command=self._new_chat,
            bg=BG_SIDEBAR, fg=TEXT_PRI,
            relief="flat", font=FONT_UI,
            activebackground=BG_HOVER,
            activeforeground=WHITE,
            cursor="hand2", anchor="w",
            padx=14, pady=8,
            bd=1, highlightbackground=BORDER)
        new_btn.pack(fill="x", padx=10, pady=(0,8))
        new_btn.bind("<Enter>", lambda e: new_btn.config(bg=BG_HOVER))
        new_btn.bind("<Leave>", lambda e: new_btn.config(bg=BG_SIDEBAR))

        # Chat history list
        tk.Label(self.sidebar, text="  Recent Chats",
                 bg=BG_SIDEBAR, fg=TEXT_SEC,
                 font=("Segoe UI",8,"bold")).pack(anchor="w", padx=14, pady=(4,2))

        self.chat_list_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        self.chat_list_frame.pack(fill="both", expand=True, padx=6)

        # Bottom model selector
        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=10, pady=8)
        model_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        model_frame.pack(fill="x", padx=10, pady=(0,10))
        tk.Label(model_frame, text="Model:", bg=BG_SIDEBAR, fg=TEXT_SEC,
                 font=FONT_SMALL).pack(side="left", padx=(4,6))
        models = ["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo"]
        model_menu = tk.OptionMenu(model_frame, self.model_var, *models)
        model_menu.config(bg=BG_INPUT, fg=TEXT_PRI, relief="flat",
                          font=FONT_SMALL, activebackground=BG_HOVER,
                          highlightthickness=0, bd=0)
        model_menu["menu"].config(bg=BG_INPUT, fg=TEXT_PRI, relief="flat")
        model_menu.pack(side="left", fill="x", expand=True)

        # ── Main area ─────────────────────────────────────────────
        main = tk.Frame(self.root, bg=BG_MAIN)
        main.pack(side="left", fill="both", expand=True)

        # Header bar
        header = tk.Frame(main, bg=BG_MAIN, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        self.chat_title_var = tk.StringVar(value="New Conversation")
        tk.Label(header, textvariable=self.chat_title_var,
                 bg=BG_MAIN, fg=TEXT_PRI,
                 font=("Segoe UI",12,"bold")).pack(side="left", padx=20, pady=14)
        # Clear button
        clr_btn = tk.Button(header, text="🗑  Clear",
                            command=self._clear_chat,
                            bg=BG_MAIN, fg=TEXT_SEC,
                            relief="flat", font=FONT_SMALL,
                            activebackground=BG_HOVER,
                            cursor="hand2")
        clr_btn.pack(side="right", padx=16, pady=14)

        tk.Frame(main, bg=BORDER, height=1).pack(fill="x")

        # Messages area
        self.msg_canvas = tk.Canvas(main, bg=BG_MAIN,
                                    highlightthickness=0, bd=0)
        self.msg_canvas.pack(fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(main, orient="vertical",
                                       command=self.msg_canvas.yview)
        self.msg_canvas.configure(yscrollcommand=self.scrollbar.set)

        # Layout canvas + scrollbar side by side
        self.msg_canvas.pack_forget()
        self.scrollbar.pack_forget()

        msg_area = tk.Frame(main, bg=BG_MAIN)
        msg_area.pack(fill="both", expand=True)

        self.scrollbar2 = tk.Scrollbar(msg_area, bg=BG_MAIN,
                                        troughcolor=BG_MAIN,
                                        relief="flat", width=6)
        self.scrollbar2.pack(side="right", fill="y")

        self.msg_canvas2 = tk.Canvas(msg_area, bg=BG_MAIN,
                                      highlightthickness=0,
                                      yscrollcommand=self.scrollbar2.set)
        self.msg_canvas2.pack(side="left", fill="both", expand=True)
        self.scrollbar2.config(command=self.msg_canvas2.yview)

        self.msg_frame = tk.Frame(self.msg_canvas2, bg=BG_MAIN)
        self.msg_frame_id = self.msg_canvas2.create_window(
            (0,0), window=self.msg_frame, anchor="nw")

        self.msg_frame.bind("<Configure>", self._on_frame_configure)
        self.msg_canvas2.bind("<Configure>", self._on_canvas_configure)
        self.msg_canvas2.bind_all("<MouseWheel>", self._on_mousewheel)

        # Welcome screen
        self._show_welcome()

        # ── Input bar ──────────────────────────────────────────────
        input_outer = tk.Frame(main, bg=BG_MAIN)
        input_outer.pack(fill="x", padx=40, pady=(8,20))

        input_wrap = tk.Frame(input_outer, bg=BG_INPUT,
                               highlightbackground=BORDER,
                               highlightthickness=1)
        input_wrap.pack(fill="x")

        self.input_box = tk.Text(input_wrap, height=3,
                                  bg=BG_INPUT, fg=TEXT_PRI,
                                  insertbackground=TEXT_PRI,
                                  relief="flat", font=FONT_MSG,
                                  wrap="word", padx=14, pady=10)
        self.input_box.pack(side="left", fill="both", expand=True)
        self.input_box.bind("<Return>",       self._on_enter)
        self.input_box.bind("<Shift-Return>", lambda e: None)
        self.input_box.insert("1.0", "Message ChatGPT…")
        self.input_box.config(fg=TEXT_SEC)
        self.input_box.bind("<FocusIn>",  self._ph_in)
        self.input_box.bind("<FocusOut>", self._ph_out)

        send_btn = tk.Button(input_wrap, text="↑",
                             command=self._send,
                             bg=SEND_BG, fg=SEND_FG,
                             relief="flat",
                             font=("Segoe UI",14,"bold"),
                             activebackground=ACCENT_H,
                             cursor="hand2",
                             width=3, pady=6)
        send_btn.pack(side="right", padx=8, pady=8)

        tk.Label(input_outer,
                 text="ChatGPT can make mistakes. Verify important info.",
                 bg=BG_MAIN, fg=TEXT_SEC,
                 font=FONT_SMALL).pack(pady=(4,0))

        if not G4F_OK:
            tk.Label(input_outer,
                     text="⚠  g4f not installed — run: python -m pip install g4f",
                     bg=BG_MAIN, fg=DANGER,
                     font=FONT_SMALL).pack()

    # ════════════════════════════════════════════════════════════
    # WELCOME SCREEN
    # ════════════════════════════════════════════════════════════
    def _show_welcome(self):
        for w in self.msg_frame.winfo_children():
            w.destroy()

        wrap = tk.Frame(self.msg_frame, bg=BG_MAIN)
        wrap.pack(expand=True, pady=60)

        tk.Label(wrap, text="⬡", bg=BG_MAIN, fg=ACCENT,
                 font=("Segoe UI",40)).pack()
        tk.Label(wrap, text="How can I help you today?",
                 bg=BG_MAIN, fg=TEXT_PRI,
                 font=("Segoe UI",20,"bold")).pack(pady=(10,20))

        # Suggestion chips
        suggestions = [
            ("💡", "Explain quantum computing\nin simple terms"),
            ("✍", "Write a cover letter\nfor a software engineer role"),
            ("🐍", "Debug my Python code\nand explain the fix"),
            ("📋", "Summarise a long article\ninto key bullet points"),
        ]
        chips = tk.Frame(wrap, bg=BG_MAIN)
        chips.pack()
        for icon, text in suggestions:
            chip = tk.Frame(chips, bg=BG_INPUT,
                            highlightbackground=BORDER,
                            highlightthickness=1)
            chip.pack(side="left", padx=6, pady=4)
            tk.Label(chip, text=icon, bg=BG_INPUT, fg=TEXT_PRI,
                     font=("Segoe UI",16)).pack(padx=14, pady=(10,4))
            tk.Label(chip, text=text, bg=BG_INPUT, fg=TEXT_SEC,
                     font=("Segoe UI",9), justify="center").pack(padx=14, pady=(0,10))
            full = text.replace("\n"," ")
            chip.bind("<Button-1>", lambda e, t=full: self._send_text(t))
            for child in chip.winfo_children():
                child.bind("<Button-1>", lambda e, t=full: self._send_text(t))
            chip.bind("<Enter>", lambda e, c=chip: c.config(bg=BG_HOVER))
            chip.bind("<Leave>", lambda e, c=chip: c.config(bg=BG_INPUT))

    # ════════════════════════════════════════════════════════════
    # CHAT SESSIONS
    # ════════════════════════════════════════════════════════════
    def _new_chat(self):
        self.history = []
        self.chat_title_var.set("New Conversation")
        self._show_welcome()
        self._refresh_sidebar()

    def _clear_chat(self):
        self.history = []
        self._show_welcome()

    def _refresh_sidebar(self):
        for w in self.chat_list_frame.winfo_children():
            w.destroy()
        for i, h in enumerate(self.chats[-15:][::-1]):
            title = h.get("title","Chat")
            btn = tk.Button(self.chat_list_frame,
                            text=f"💬  {title[:26]}",
                            command=lambda h=h: self._load_chat(h),
                            bg=BG_SIDEBAR, fg=TEXT_PRI,
                            relief="flat", font=FONT_SMALL,
                            activebackground=BG_HOVER,
                            cursor="hand2", anchor="w",
                            padx=10, pady=6)
            btn.pack(fill="x", pady=1)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=BG_HOVER))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BG_SIDEBAR))

    def _load_chat(self, session):
        self.history = session["history"].copy()
        self.chat_title_var.set(session.get("title","Chat"))
        for w in self.msg_frame.winfo_children():
            w.destroy()
        for msg in self.history:
            self._render_bubble(msg["role"], msg["content"])
        self._scroll_bottom()

    # ════════════════════════════════════════════════════════════
    # SEND / RECEIVE
    # ════════════════════════════════════════════════════════════
    def _ph_in(self, e):
        if self.input_box.get("1.0","end-1c") == "Message ChatGPT…":
            self.input_box.delete("1.0",tk.END)
            self.input_box.config(fg=TEXT_PRI)

    def _ph_out(self, e):
        if not self.input_box.get("1.0","end-1c").strip():
            self.input_box.insert("1.0","Message ChatGPT…")
            self.input_box.config(fg=TEXT_SEC)

    def _on_enter(self, event):
        if event.state & 0x1:   # Shift+Enter = newline
            return
        self._send()
        return "break"

    def _send_text(self, text):
        self.input_box.delete("1.0",tk.END)
        self.input_box.config(fg=TEXT_PRI)
        self.input_box.insert("1.0",text)
        self._send()

    def _send(self):
        if self.typing: return
        msg = self.input_box.get("1.0","end-1c").strip()
        if not msg or msg == "Message ChatGPT…": return

        self.input_box.delete("1.0",tk.END)
        self.input_box.config(fg=TEXT_PRI)

        # clear welcome if first message
        first = len(self.history) == 0
        if first:
            for w in self.msg_frame.winfo_children():
                w.destroy()

        self.history.append({"role":"user","content":msg})
        self._render_bubble("user", msg)
        self._scroll_bottom()

        # typing indicator
        self.typing = True
        self.typing_label = self._render_typing()
        self._scroll_bottom()

        # set chat title from first message
        if first:
            title = msg[:35] + ("…" if len(msg)>35 else "")
            self.chat_title_var.set(title)
            self.chats.append({"title":title,"history":self.history})
            self._refresh_sidebar()

        threading.Thread(target=self._get_response, daemon=True).start()

    def _get_response(self):
        if not G4F_OK:
            reply = ("g4f is not installed.\n\n"
                     "Run:  python -m pip install g4f\n\n"
                     "Then restart the app.")
        else:
            try:
                client = Client()
                response = client.chat.completions.create(
                    model=self.model_var.get(),
                    messages=self.history,
                )
                reply = response.choices[0].message.content
            except Exception as ex:
                reply = f"⚠ Error: {ex}\n\nTry a different model or check your internet connection."

        self.history.append({"role":"assistant","content":reply})
        self.root.after(0, lambda: self._on_response(reply))

    def _on_response(self, reply):
        # remove typing indicator
        if hasattr(self,"typing_label") and self.typing_label.winfo_exists():
            self.typing_label.destroy()
        self.typing = False
        self._render_bubble("assistant", reply)
        self._scroll_bottom()
        # update stored history
        if self.chats:
            self.chats[-1]["history"] = self.history.copy()

    # ════════════════════════════════════════════════════════════
    # BUBBLE RENDERING
    # ════════════════════════════════════════════════════════════
    def _render_bubble(self, role, content):
        is_user = role == "user"

        row = tk.Frame(self.msg_frame, bg=BG_MAIN)
        row.pack(fill="x", pady=2)

        inner = tk.Frame(row, bg=BG_USER if is_user else BG_BOT)
        inner.pack(fill="x", padx=0)

        # avatar + name row
        meta = tk.Frame(inner, bg=BG_USER if is_user else BG_BOT)
        meta.pack(fill="x", padx=60, pady=(12,4))

        avatar_txt = "You" if is_user else "⬡"
        avatar_bg  = ACCENT if not is_user else "#444"
        av = tk.Label(meta, text=avatar_txt,
                      bg=avatar_bg, fg=WHITE,
                      font=("Segoe UI",9,"bold"),
                      width=3, pady=2)
        av.pack(side="left")

        name = "You" if is_user else "ChatGPT"
        tk.Label(meta, text=f"  {name}",
                 bg=BG_USER if is_user else BG_BOT,
                 fg=TEXT_PRI,
                 font=("Segoe UI",10,"bold")).pack(side="left")

        ts = datetime.datetime.now().strftime("%H:%M")
        tk.Label(meta, text=ts,
                 bg=BG_USER if is_user else BG_BOT,
                 fg=TEXT_SEC,
                 font=FONT_TIME).pack(side="left", padx=8)

        # message content
        msg_bg = BG_USER if is_user else BG_BOT

        # Detect code blocks and render separately
        parts = self._split_code(content)
        for ptype, ptext in parts:
            if ptype == "code":
                code_wrap = tk.Frame(inner, bg="#1e1e1e",
                                     highlightbackground="#3a3a3a",
                                     highlightthickness=1)
                code_wrap.pack(fill="x", padx=60, pady=4)
                # language label
                lang_bar = tk.Frame(code_wrap, bg="#2d2d2d")
                lang_bar.pack(fill="x")
                lang = ptext.split("\n")[0] if ptext else ""
                code_body = "\n".join(ptext.split("\n")[1:]) if "\n" in ptext else ptext
                tk.Label(lang_bar, text=lang or "code",
                         bg="#2d2d2d", fg=TEXT_SEC,
                         font=("Segoe UI",8)).pack(side="left",padx=10,pady=4)
                copy_btn = tk.Button(lang_bar, text="Copy",
                                     command=lambda t=code_body: self._copy(t),
                                     bg="#2d2d2d", fg=TEXT_SEC,
                                     relief="flat", font=("Segoe UI",8),
                                     cursor="hand2")
                copy_btn.pack(side="right",padx=10,pady=4)
                code_lbl = tk.Text(code_wrap, bg="#1e1e1e", fg="#abb2bf",
                                   font=FONT_CODE, relief="flat",
                                   wrap="none", padx=14, pady=8,
                                   state="normal")
                code_lbl.insert("1.0", code_body)
                code_lbl.config(state="disabled",
                                height=min(code_body.count("\n")+1, 20))
                code_lbl.pack(fill="x")
            else:
                lbl = tk.Label(inner,
                               text=ptext,
                               bg=msg_bg,
                               fg=TEXT_BOT if not is_user else TEXT_USER,
                               font=FONT_MSG,
                               wraplength=750,
                               justify="left",
                               anchor="w")
                lbl.pack(fill="x", padx=60, pady=(0,2))

        # bottom padding
        tk.Frame(inner, bg=msg_bg, height=8).pack()

    def _render_typing(self):
        row = tk.Frame(self.msg_frame, bg=BG_MAIN)
        row.pack(fill="x", pady=2)
        inner = tk.Frame(row, bg=BG_BOT)
        inner.pack(fill="x")
        lbl = tk.Label(inner,
                       text="   ⬡  ChatGPT  ●●●  Thinking…",
                       bg=BG_BOT, fg=TEXT_SEC,
                       font=("Segoe UI",10,"italic"),
                       padx=60, pady=16)
        lbl.pack(anchor="w")
        return row

    def _split_code(self, text):
        """Split message into (type, content) parts: 'text' or 'code'."""
        parts = []
        segments = text.split("```")
        for i, seg in enumerate(segments):
            if i % 2 == 0:
                if seg.strip():
                    parts.append(("text", seg.strip()))
            else:
                parts.append(("code", seg))
        return parts if parts else [("text", text)]

    def _copy(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    # ════════════════════════════════════════════════════════════
    # SCROLL HELPERS
    # ════════════════════════════════════════════════════════════
    def _on_frame_configure(self, e):
        self.msg_canvas2.configure(scrollregion=self.msg_canvas2.bbox("all"))

    def _on_canvas_configure(self, e):
        self.msg_canvas2.itemconfig(self.msg_frame_id, width=e.width)

    def _on_mousewheel(self, e):
        self.msg_canvas2.yview_scroll(int(-1*(e.delta/120)), "units")

    def _scroll_bottom(self):
        self.root.after(50, lambda: self.msg_canvas2.yview_moveto(1.0))


# ── Entry ────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    ChatApp(root)
    root.mainloop()
