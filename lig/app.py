# -*- coding: utf-8 -*-
"""
رابط گرافیکی برنامهٔ جدول لیگ برتر ایران
- RTL (راست‌به‌چپ) با تنظیمات Windows
- تب‌ها: جدول | تیم‌ها | مسابقات | پیش‌بینی | واردات از اسکرین‌شات
- کلیک روی هر تیم => صفحهٔ جزئیات تیم (اخبار، ۵ بازی گذشته، ۵ بازی پیش‌رو، قدرت، بازیکنان)
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from lig import data, ocr_import


def resource_path(rel):
    """مسئول فایل‌های الحاقی در حالت EXE (PyInstaller) و حالت عادی."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        p = os.path.join(base, rel)
        if os.path.exists(p):
            return p
    # حالت توسعه: پوشهٔ assets کنار پروژه
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, rel)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT = "Segoe UI"
TEAM_COLORS = ["#2c7be5", "#e74c3c", "#f1c40f", "#2ecc71", "#9b59b6",
               "#e67e22", "#1abc9c", "#d35400", "#3498db", "#c0392b"]


def make_rtl(widget):
    """فعال‌سازی راست‌به‌چپ برای ویجت و فرزندان آن."""
    try:
        widget.tk.call("tk", "scaling", 1.25)
    except Exception:
        pass


def apply_rtl(widget):
    """اعمال -direction rtl روی همهٔ ویجت‌های دارای این گزینه (برخورد امن)."""
    stack = [widget]
    while stack:
        w = stack.pop()
        try:
            w.configure(**{"-direction": "rtl"})
        except Exception:
            pass
        stack.extend(w.winfo_children())


class LeagueApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("جدول لیگ برتر ایران ⚽")
        self.geometry("1180x720")
        self.minsize(940, 600)
        self._set_icon()
        data.init_db()
        self.season_var = ctk.StringVar(value=data.get_setting("season", ""))
        self._build_ui()
        self.refresh_all()
        try:
            apply_rtl(self)
        except Exception:
            pass

    # ---------------- آیکون برنامه ----------------
    def _set_icon(self):
        try:
            ico = resource_path(os.path.join("assets", "LeaguePro.ico"))
            png = resource_path(os.path.join("assets", "LeaguePro.png"))
            if sys.platform == "win32" and os.path.exists(ico):
                self.iconbitmap(ico)
            if os.path.exists(png):
                from PIL import Image
                self._icon_img = tk.PhotoImage(file=png)
                self.iconphoto(True, self._icon_img)
        except Exception:
            pass

    # ---------------- ساخت رابط ----------------
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0, fg_color="#151a28")
        header.grid(row=0, column=0, sticky="we")
        ctk.CTkLabel(header, text="⚽  جدول لیگ برتر خلیج فارس",
                     font=(FONT, 22, "bold")).pack(side="right", padx=18, pady=10)
        season_box = ctk.CTkFrame(header, fg_color="transparent")
        season_box.pack(side="left", padx=14)
        ctk.CTkLabel(season_box, text="فصل:", font=(FONT, 13)).pack(side="right")
        self.season_entry = ctk.CTkEntry(season_box, textvariable=self.season_var,
                                         width=110, font=(FONT, 13), placeholder_text="مثلاً 1404-1405")
        self.season_entry.pack(side="right", padx=6)
        ctk.CTkButton(season_box, text="ثبت فصل", width=80, height=28,
                      command=self._set_season).pack(side="right", padx=4)

        self.tabs = ctk.CTkTabview(self, anchor="e")
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.tab_table = self.tabs.add("🏆 جدول")
        self.tab_teams = self.tabs.add("🛃 تیم‌ها")
        self.tab_matches = self.tabs.add("📅 مسابقات")
        self.tab_predict = self.tabs.add("🔮 پیش‌بینی")
        self.tab_ocr = self.tabs.add("📸 واردات از اسکرین‌شات")

        self._build_table_tab()
        self._build_teams_tab()
        self._build_matches_tab()
        self._build_predict_tab()
        self._build_ocr_tab()

    def _set_season(self):
        s = self.season_var.get().strip()
        data.set_setting("season", s)
        self.refresh_all()
        self._toast(f"فصل «{s or '(بدون نام)'}» ثبت شد")

    def _toast(self, msg):
        messagebox.showinfo("لیگ برتر", msg)

    # ---------------- تب جدول ----------------
    def _build_table_tab(self):
        wrap = ctk.CTkFrame(self.tab_table, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=6, pady=6)

        cols = ("رتبه", "تیم", "بازی", "برد", "تساوی", "باخت",
                "گل زده", "گل خورده", "تفاضل", "امتیاز", "قدرت", "فرم")
        widths = (52, 190, 52, 48, 56, 52, 66, 72, 60, 66, 66, 120)
        tree_frame = ctk.CTkFrame(wrap)
        tree_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="tree", selectmode="browse")
        vsb = tk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="left", fill="y")
        self.tree.pack(fill="both", expand=True)

        self.tree.heading("#0", text="تیم", anchor="e")
        self.tree.column("#0", width=200, anchor="e", stretch=True)
        for name, wd in zip(cols[1:], widths[1:]):
            self.tree.heading(name, text=name, anchor="center")
            self.tree.column(name, width=wd, anchor="center", stretch=False)

        self.tree.tag_configure("odd", background="#1b2233")
        self.tree.tag_configure("even", background="#151a28")
        self.tree.tag_configure("champ", background="#12351f")
        self.tree.tag_configure("releg", background="#3a1620")
        for i in range(len(TEAM_COLORS)):
            self.tree.tag_configure(f"team{i}", foreground=TEAM_COLORS[i])
        self.tree.bind("<Double-1>", self._open_team_from_tree)
        self.tree.bind("<Return>", self._open_team_from_tree)

        hint = ctk.CTkLabel(wrap, text="💡 با دابل‌کلیک روی هر تیم، صفحهٔ جزئیات آن باز می‌شود",
                            font=(FONT, 12), text_color="gray")
        hint.pack(anchor="e", pady=(4, 0))

    def _refresh_table(self):
        t = self.tree
        sel = t.selection()
        sel_id = sel[0] if sel else None
        t.delete(*t.get_children())
        table = data.standings(self.season_var.get().strip() or None)
        n = len(table)
        team_ids = {}
        for idx, row in enumerate(table):
            tags = []
            if idx < 3:
                tags.append("champ")
            elif n and idx >= n - max(1, min(2, n // 8)):
                tags.append("releg")
            else:
                tags.append("odd" if idx % 2 else "even")
            tags.append(f"team{row['id'] % len(TEAM_COLORS)}")
            form = "".join({"W": "●", "D": "○", "L": "✕"}[x] for x in row["form"])
            vals = (row["played"], row["w"], row["d"], row["l"],
                    row["gf"], row["ga"], row["gd"], row["pts"],
                    f"{row['power']:.0f}", form)
            iid = t.insert("", "end", text=f"{row['rank']}   {row['name']}", values=vals,
                           tags=tags, iid=str(row["id"]))
            team_ids[iid] = row["id"]
        self._team_ids = team_ids
        if sel_id and t.exists(sel_id):
            t.selection_set(sel_id)

    def _open_team_from_tree(self, _e=None):
        sel = self.tree.selection()
        if not sel:
            return
        tid = int(sel[0])
        TeamDetailWindow(self, tid)

    # ---------------- تب تیم‌ها ----------------
    def _build_teams_tab(self):
        right = ctk.CTkFrame(self.tab_teams)
        right.pack(side="right", fill="both", expand=True, padx=6, pady=6)
        left = ctk.CTkFrame(self.tab_teams, width=340)
        left.pack(side="left", fill="y", padx=6, pady=6)
        left.pack_propagate(False)

        ctk.CTkLabel(right, text="فهرست تیم‌ها (برای افزودن/ویرایش انتخاب کنید)",
                     font=(FONT, 14, "bold")).pack(anchor="e", pady=(6, 2), padx=10)
        listf = ctk.CTkFrame(right, fg_color="transparent")
        listf.pack(fill="both", expand=True, padx=10, pady=4)
        self.team_list = tk.Listbox(listf, font=(FONT, 14), bg="#151a28", fg="white",
                                    selectbackground="#2c7be5", activestyle="none",
                                    exportselection=False)
        sb = tk.Scrollbar(listf, command=self.team_list.yview)
        self.team_list.configure(yscrollcommand=sb.set)
        sb.pack(side="left", fill="y")
        self.team_list.pack(fill="both", expand=True)
        self.team_list.bind("<<ListboxSelect>>", lambda e: self._load_team_form())
        btns = ctk.CTkFrame(right, fg_color="transparent")
        btns.pack(fill="x", padx=10, pady=6)
        ctk.CTkButton(btns, text="➕ افزودن تیم جدید", command=self._add_team, height=34).pack(side="right")
        ctk.CTkButton(btns, text="🗑 حذف تیم", fg_color="#8b2e3b", hover_color="#a53747",
                      command=self._del_team, height=34).pack(side="left")
        ctk.CTkButton(btns, text="📂 جزئیات تیم انتخابی", command=self._open_selected_team,
                      height=34).pack(side="left", padx=8)

        # فرم تیم
        ctk.CTkLabel(left, text="مشخصات تیم", font=(FONT, 15, "bold")).pack(anchor="e", pady=(10, 4), padx=12)
        self.tf = {}
        for key, label in (("name", "نام تیم"), ("city", "شهر"), ("stadium", "ورزشگاه"), ("coach", "سرمربی")):
            row = ctk.CTkFrame(left, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(row, text=label + ":", width=80, font=(FONT, 13)).pack(side="right")
            ent = ctk.CTkEntry(row, font=(FONT, 13))
            ent.pack(side="right", fill="x", expand=True)
            self.tf[key] = ent
        crow = ctk.CTkFrame(left, fg_color="transparent")
        crow.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(crow, text="رنگ:", width=80, font=(FONT, 13)).pack(side="right")
        self.color_var = ctk.StringVar(value=TEAM_COLORS[0])
        self.color_menu = ctk.CTkOptionMenu(crow, variable=self.color_var, values=TEAM_COLORS, width=140)
        self.color_menu.pack(side="right")
        ctk.CTkButton(left, text="💾 ذخیرهٔ تغییرات", height=34, command=self._save_team_form)\
            .pack(fill="x", padx=12, pady=10)

    def _selected_team_id(self):
        sel = self.team_list.curselection()
        if not sel:
            return None
        return self._teams_list[sel[0]]["id"]

    def _refresh_teams(self):
        self.team_list.delete(0, "end")
        self._teams_list = data.list_teams()
        table = {x["id"]: x for x in data.standings()}
        for t in self._teams_list:
            s = table.get(t["id"], {})
            self.team_list.insert("end",
                                  f"  {s.get('rank','-')}. {t['name']}  ({s.get('pts',0)} امتیاز، قدرت {t['power']:.0f})")

    def _add_team(self):
        name = self.tf["name"].get().strip()
        if not name:
            messagebox.showwarning("لیگ برتر", "ابتدا نام تیم را در فرم سمت چپ بنویسید، سپس «افزودن» را بزنید.")
            return
        try:
            data.add_team(name, self.tf["city"].get(), self.tf["stadium"].get(),
                          self.tf["coach"].get(), self.color_var.get())
        except Exception as e:
            messagebox.showerror("خطا", str(e))
            return
        self._clear_team_form()
        self.refresh_all()
        self._toast(f"تیم «{name}» افزوده شد")

    def _clear_team_form(self):
        for k, e in self.tf.items():
            e.delete(0, "end")
        self.color_var.set(TEAM_COLORS[0])

    def _del_team(self):
        tid = self._selected_team_id()
        if not tid:
            return
        t = data.get_team(tid)
        if messagebox.askyesno("حذف تیم", f"تیم «{t['name']}» با همهٔ بازی‌ها و بازیکنانش حذف شود؟"):
            data.delete_team(tid)
            self._clear_team_form()
            self.refresh_all()

    def _open_selected_team(self):
        tid = self._selected_team_id()
        if tid:
            TeamDetailWindow(self, tid)

    def _load_team_form(self):
        tid = self._selected_team_id()
        if not tid:
            return
        t = data.get_team(tid)
        self._clear_team_form()
        for k in ("name", "city", "stadium", "coach"):
            self.tf[k].insert(0, t[k] or "")
        self.color_var.set(t["color"] or TEAM_COLORS[0])

    def _save_team_form(self):
        tid = self._selected_team_id()
        if not tid:
            messagebox.showwarning("لیگ برتر", "ابتدا یک تیم را از فهرست انتخاب کنید.")
            return
        name = self.tf["name"].get().strip()
        if not name:
            messagebox.showwarning("لیگ برتر", "نام تیم نمی‌تواند خالی باشد.")
            return
        data.update_team(tid, name=name, city=self.tf["city"].get().strip(),
                         stadium=self.tf["stadium"].get().strip(), coach=self.tf["coach"].get().strip(),
                         color=self.color_var.get())
        self.refresh_all()
        self._toast("تغییرات ذخیره شد")

    # ---------------- تب مسابقات ----------------
    def _build_matches_tab(self):
        top = ctk.CTkFrame(self.tab_matches)
        top.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(top, text="➕ ثبت بازی (دستی)", font=(FONT, 14, "bold")).pack(anchor="e", padx=10, pady=(6, 0))
        row = ctk.CTkFrame(top, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=6)
        self.home_var = ctk.StringVar()
        self.away_var = ctk.StringVar()
        self.date_var = ctk.StringVar()
        self.week_var = ctk.StringVar(value="1")
        self.hg_var = ctk.StringVar()
        self.ag_var = ctk.StringVar()
        self.venue_var = ctk.StringVar()

        def mk(label, var, w=150, ph=""):
            box = ctk.CTkFrame(row, fg_color="transparent")
            box.pack(side="right", padx=5)
            ctk.CTkLabel(box, text=label, font=(FONT, 12)).pack(anchor="e")
            return ctk.CTkEntry(box, textvariable=var, width=w, font=(FONT, 13), placeholder_text=ph)

        def mk_combo(label, var, w=160):
            box = ctk.CTkFrame(row, fg_color="transparent")
            box.pack(side="right", padx=5)
            ctk.CTkLabel(box, text=label, font=(FONT, 12)).pack(anchor="e")
            return ctk.CTkComboBox(box, variable=var, width=w, font=(FONT, 13))

        self.home_menu = mk_combo("میزبان", self.home_var)
        self.away_menu = mk_combo("میهمان", self.away_var)
        mk("تاریخ", self.date_var, 110, "1404/08/05")
        mk("هفته", self.week_var, 55)
        mk("گل میزبان", self.hg_var, 70)
        mk("گل میهمان", self.ag_var, 70)
        mk("محل", self.venue_var, 120)
        ctk.CTkButton(row, text="💾 ثبت بازی", height=34, command=self._add_match)\
            .pack(side="right", padx=10, pady=12)

        body = ctk.CTkFrame(self.tab_matches, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=6, pady=4)
        ctk.CTkLabel(body, text="فهرست بازی‌ها — نتایج را می‌توانید بعداً با دو کلیک ویرایش کنید",
                     font=(FONT, 13, "bold")).pack(anchor="e", pady=(2, 4))
        lf = ctk.CTkFrame(body)
        lf.pack(fill="both", expand=True)
        self.match_scroll = ctk.CTkScrollableFrame(lf, fg_color="#151a28")
        self.match_scroll.pack(fill="both", expand=True, padx=2, pady=2)

    def _add_match(self, home=None, away=None, hg=None, ag=None, date=None, week=None, source="manual"):
        names = [t["name"] for t in data.list_teams()]
        hname = home or self.home_var.get().strip()
        aname = away or self.away_var.get().strip()
        th = data.find_team_by_name(hname)
        ta = data.find_team_by_name(aname)
        if not th or not ta:
            messagebox.showwarning("لیگ برتر", "نام دو تیم را دقیق از فهرست انتخاب کنید.")
            return
        def gi(v):
            v = str(v).strip()
            return int(v) if v.isdigit() else None
        h_goals = hg if hg is not None else gi(self.hg_var.get())
        a_goals = ag if ag is not None else gi(self.ag_var.get())
        d = date if date is not None else self.date_var.get().strip()
        wk = week if week is not None else (gi(self.week_var.get()) or 0)
        try:
            data.add_match(th["id"], ta["id"], date=d, week=wk, home_goals=h_goals,
                           away_goals=a_goals, season=self.season_var.get().strip(),
                           venue=self.venue_var.get().strip(), source=source)
        except Exception as e:
            messagebox.showerror("خطا", str(e))
            return
        for v in (self.hg_var, self.ag_var, self.date_var, self.venue_var):
            v.set("")
        self.refresh_all()

    def _refresh_matches(self):
        for w in self.match_scroll.winfo_children():
            w.destroy()
        ms = data.list_matches(season=self.season_var.get().strip() or None)
        if not ms:
            ctk.CTkLabel(self.match_scroll, text="هنوز بازی‌ای ثبت نشده است.",
                         font=(FONT, 14), text_color="gray").pack(pady=30)
            return
        for m in ms:
            row = ctk.CTkFrame(self.match_scroll, fg_color="#1b2233", corner_radius=8)
            row.pack(fill="x", padx=6, pady=3)
            res = f"{m['home_goals']} - {m['away_goals']}" if m["status"] == "finished" else "برنامه‌ریزی"
            txt = (f"[{m['week'] or '-'}]  {m['date'] or '---'}   "
                   f"{m['home_name']}   {res}   {m['away_name']}"
                   + (f"   | {m['venue']}" if m["venue"] else "")
                   + (f"   (منبع: {m['source']})" if m["source"] != "manual" else ""))
            ctk.CTkLabel(row, text=txt, font=(FONT, 13)).pack(side="right", padx=10, pady=8)
            ctk.CTkButton(row, text="🗑", width=36, fg_color="#8b2e3b",
                          command=lambda mid=m["id"]: self._del_match(mid)).pack(side="left", padx=6)
            if m["status"] != "finished":
                ctk.CTkButton(row, text="⚽ ثبت نتیجه", width=90,
                              command=lambda mm=m: self._result_dialog(mm)).pack(side="left", padx=4)

    def _del_match(self, mid):
        if messagebox.askyesno("حذف بازی", "این بازی حذف شود؟"):
            data.delete_match(mid)
            self.refresh_all()

    def _result_dialog(self, m):
        dlg = ctk.CTkToplevel(self)
        dlg.title("ثبت نتیجه")
        dlg.geometry("320x220")
        dlg.transient(self)
        dlg.grab_set()
        ctk.CTkLabel(dlg, text=f"{m['home_name']}  مقابل  {m['away_name']}",
                     font=(FONT, 14, "bold")).pack(pady=14)
        hv = ctk.StringVar(); av = ctk.StringVar()
        row = ctk.CTkFrame(dlg, fg_color="transparent"); row.pack(pady=6)
        ctk.CTkEntry(row, textvariable=hv, width=70, font=(FONT, 18)).pack(side="right", padx=8)
        ctk.CTkLabel(row, text="-", font=(FONT, 18)).pack(side="right")
        ctk.CTkEntry(row, textvariable=av, width=70, font=(FONT, 18)).pack(side="right", padx=8)
        def ok():
            if not hv.get().isdigit() or not av.get().isdigit():
                messagebox.showwarning("لیگ برتر", "گل‌ها باید عدد باشند", parent=dlg)
                return
            data.update_match(m["id"], home_goals=int(hv.get()), away_goals=int(av.get()))
            dlg.destroy(); self.refresh_all()
        ctk.CTkButton(dlg, text="ثبت", width=120, height=34, command=ok).pack(pady=10)

    # ---------------- تب پیش‌بینی ----------------
    def _build_predict_tab(self):
        box = ctk.CTkFrame(self.tab_predict)
        box.pack(fill="both", expand=True, padx=6, pady=6)
        ctk.CTkLabel(box, text="🔮 پیش‌بینی نتیجهٔ بازی (مدل پواسون روی داده‌های ذخیره‌شده)",
                     font=(FONT, 15, "bold")).pack(anchor="e", padx=12, pady=(10, 2))
        row = ctk.CTkFrame(box, fg_color="transparent"); row.pack(fill="x", padx=12, pady=8)
        self.ph_home = ctk.StringVar(); self.ph_away = ctk.StringVar()
        self.ph_home_menu = ctk.CTkComboBox(row, variable=self.ph_home, width=180, font=(FONT, 14))
        self.ph_away_menu = ctk.CTkComboBox(row, variable=self.ph_away, width=180, font=(FONT, 14))
        ctk.CTkLabel(row, text="میزبان:", font=(FONT, 13)).pack(side="right")
        self.ph_home_menu.pack(side="right", padx=6)
        ctk.CTkLabel(row, text="میهمان:", font=(FONT, 13)).pack(side="right", padx=(16, 0))
        self.ph_away_menu.pack(side="right", padx=6)
        ctk.CTkButton(row, text="پیش‌بینی کن", height=36, command=self._predict).pack(side="right", padx=14)
        self.pred_out = ctk.CTkTextbox(box, font=(FONT, 14), wrap="word")
        self.pred_out.pack(fill="both", expand=True, padx=12, pady=12)
        self.pred_out.insert("end", "تیم‌ها را انتخاب کنید و «پیش‌بینی کن» را بزنید.\n"
                                   "هرچه بازی و آمار بیشتری وارد کنید (دستی یا از اسکرین‌شات)، "
                                   "پیش‌بینی دقیق‌تر می‌شود.")
        self.pred_out.configure(state="disabled")

    def _predict(self):
        th = data.find_team_by_name(self.ph_home.get())
        ta = data.find_team_by_name(self.ph_away.get())
        if not th or not ta or th["id"] == ta["id"]:
            messagebox.showwarning("لیگ برتر", "دو تیم متفاوت انتخاب کنید.")
            return
        p = data.predict_match(th["id"], ta["id"], self.season_var.get().strip() or None)
        txt = (f"پیش‌بینی:  {th['name']}  {p['score']}  {ta['name']}\n\n"
               f"احتمال برد میزبان : {p['p_home']*100:.1f}%\n"
               f"احتمال مساوی      : {p['p_draw']*100:.1f}%\n"
               f"احتمال برد میهمان : {p['p_away']*100:.1f}%\n\n"
               f"گل مورد انتظار میزبان: {p['mu_home']}   میهمان: {p['mu_away']}\n"
               f"قدرت میزبان: {th['power']:.0f}   قدرت میهمان: {ta['power']:.0f}\n\n"
               "⚠ این پیش‌بینی صرفاً آماری است و مبنای قطعیت ندارد.")
        self.pred_out.configure(state="normal")
        self.pred_out.delete("1.0", "end")
        self.pred_out.insert("end", txt)
        self.pred_out.configure(state="disabled")

    # ---------------- تب OCR ----------------
    def _build_ocr_tab(self):
        box = ctk.CTkFrame(self.tab_ocr)
        box.pack(fill="both", expand=True, padx=6, pady=6)
        ctk.CTkLabel(box, text="📸 واردات اطلاعات از اسکرین‌شات جدول یا نتایج",
                     font=(FONT, 15, "bold")).pack(anchor="e", padx=12, pady=(10, 2))
        note = ("روش کار: ۱) از جدول لیگ (مثلاً از سایت football365 یا varsary) اسکرین‌شات بگیرید "
                "(Win+Shift+S)  ۲) فایل تصویر را انتخاب کنید یا دکمهٔ «کلیپ‌بورد» را بزنید  "
                "۳) متن استخراج‌شده را بررسی و در صورت لزوم دستی اصلاح کنید  ۴) «تحلیل» و سپس "
                "«ذخیره در برنامه» را بزنید.\n"
                "نکته: برای OCR فارسی بهتر است Tesseract با زبان fas نصب باشد؛ اگر نبود، متن را "
                "خودتان از روی تصویر در کادر پایین تایپ/چسبانی کنید — پارسر همان را می‌فهمد.")
        ctk.CTkLabel(box, text=note, font=(FONT, 12), justify="right",
                     wraplength=1000, text_color="#9aa5c0").pack(anchor="e", padx=12)

        row = ctk.CTkFrame(box, fg_color="transparent"); row.pack(fill="x", padx=12, pady=8)
        ctk.CTkButton(row, text="🖼 انتخاب فایل تصویر", height=34, command=self._ocr_pick_file)\
            .pack(side="right")
        ctk.CTkButton(row, text="📋 خواندن تصویر کلیپ‌بورد", height=34, command=self._ocr_clipboard)\
            .pack(side="right", padx=8)
        ctk.CTkButton(row, text="🔍 تحلیل متن", height=34, fg_color="#1f8a4c", hover_color="#25a85c",
                      command=self._ocr_parse).pack(side="right", padx=8)
        self.ocr_status = ctk.CTkLabel(row, text="", font=(FONT, 12), text_color="#f1c40f")
        self.ocr_status.pack(side="right", padx=10)

        self.ocr_text = ctk.CTkTextbox(box, font=(FONT, 13), height=170, wrap="word")
        self.ocr_text.pack(fill="x", padx=12, pady=4)

        outframe = ctk.CTkFrame(box)
        outframe.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        self.ocr_result = ctk.CTkTextbox(outframe, font=("Consolas", 13), state="normal")
        self.ocr_result.pack(fill="both", expand=True, padx=2, pady=2)
        brow = ctk.CTkFrame(box, fg_color="transparent"); brow.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkButton(brow, text="💾 ذخیرهٔ نتایج تحلیل‌شده در برنامه", height=36,
                      fg_color="#2c7be5", command=self._ocr_save).pack(side="right")
        self._parsed_rows = []
        self._parsed_matches = []

    def _ocr_pick_file(self):
        p = filedialog.askopenfilename(title="انتخاب اسکرین‌شات",
                                       filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.webp")])
        if p:
            self._run_ocr_on_file(p)

    def _ocr_clipboard(self):
        p = ocr_import.grab_screen_clipboard_image()
        if not p:
            messagebox.showinfo("لیگ برتر",
                                "تصویری در کلیپ‌بورد پیدا نشد.\nابتدا Win+Shift+S را بزنید و از جدول "
                                "اسکرین‌شات بگیرید، سپس این دکمه را فشار دهید.")
            return
        self._run_ocr_on_file(p)

    def _run_ocr_on_file(self, path):
        archived = ocr_import.save_screenshot_copy(path)
        self.ocr_status.configure(text=f"در حال OCR… {os.path.basename(archived)}")
        self.update_idletasks()

        def work():
            try:
                txt = ocr_import.image_to_text(archived)
                self.after(0, lambda: self._ocr_done(txt))
            except Exception as e:
                self.after(0, lambda: self._ocr_failed(str(e), archived))
        import threading
        threading.Thread(target=work, daemon=True).start()

    def _ocr_done(self, txt):
        self.ocr_text.delete("1.0", "end")
        self.ocr_text.insert("end", txt)
        self.ocr_status.configure(text="متن از تصویر استخراج شد ✔")

    def _ocr_failed(self, err, archived):
        self.ocr_status.configure(text="OCR انجام نشد")
        messagebox.showwarning(
            "لیگ برتر",
            err + "\n\nمسیر تصویر آرشیو شده:\n" + archived +
            "\n\nمی‌توانید متن قابل‌مشاهدهٔ تصویر را خودتان در کادر وسط تایپ کنید و «تحلیل متن» را بزنید.")

    def _ocr_parse(self):
        raw = self.ocr_text.get("1.0", "end").strip()
        rows = ocr_import.parse_table_text(raw)
        teams = [t["name"] for t in data.list_teams()]
        matches = ocr_import.parse_matches_text(raw, teams) if teams else []
        self._parsed_rows, self._parsed_matches = rows, matches
        self.ocr_result.configure(state="normal")
        self.ocr_result.delete("1.0", "end")
        lines = []
        if rows:
            lines.append("ردیف‌های جدول شناسایی‌شده (قابل ویرایش نیست؛ در صورت خطا متن را اصلاح و دوباره تحلیل کنید):")
            for r in rows:
                lines.append(f"  • {r['team']}: بازی={r['played']} برد={r['w']} تساوی={r['d']} "
                             f"باخت={r['l']} GF={r['gf']} GA={r['ga']} GD={r['gd']} PTS={r['pts']}")
        if matches:
            lines.append("\nنتایج/بازی‌های شناسایی‌شده:")
            for m in matches:
                sc = f"{m['home_goals']}-{m['away_goals']}" if m["home_goals"] is not None else "برنامه‌ریزی"
                lines.append(f"  • {m['home_id']} {sc} {m['away_id']}")
        if not rows and not matches:
            lines.append("چیزی شناسایی نشد. مطمئن شوید هر سطر شامل «نام تیم + اعداد» است، "
                         "مثلاً:  پرسپولیس 30 21 5 4 60 20 40 68")
        self.ocr_result.insert("end", "\n".join(lines))
        self.ocr_result.configure(state="disabled")

    def _ocr_save(self):
        rows = getattr(self, "_parsed_rows", [])
        matches = getattr(self, "_parsed_matches", [])
        if not rows and not matches:
            messagebox.showwarning("لیگ برتر", "اول «تحلیل متن» را بزنید.")
            return
        added_teams = 0
        season = self.season_var.get().strip()
        for r in rows:
            t = data.find_team_by_name(r["team"])
            if not t:
                try:
                    t = {"id": data.add_team(r["team"])}
                    added_teams += 1
                except Exception:
                    continue
            # تبدیل ردیف جدول به «بازی‌های فرضی» برای پرکردن آمار:
            # یک بازی شبیه‌سازی‌شده در برابر «حریف ناشناخته» ساخته نمی‌شود؛
            # بلکه مستقیماً آمار از طریق ستون‌های ذخیرهٔ خاص نگه داشته می‌شود.
            data.set_setting(f"rowstats:{t['id']}:{season}",
                             ";".join(str(r.get(k) if r.get(k) is not None else "")
                                      for k in ("played", "w", "d", "l", "gf", "ga", "gd", "pts")))
        for m in matches:
            th = data.find_team_by_name(m["home_id"])
            ta = data.find_team_by_name(m["away_id"])
            if th and ta:
                try:
                    data.add_match(th["id"], ta["id"], home_goals=m["home_goals"],
                                   away_goals=m["away_goals"], season=season, source="ocr")
                except Exception:
                    pass
        self.refresh_all()
        self._toast(f"ذخیره شد: {added_teams} تیم جدید، {len(rows)} ردیف آمار، {len(matches)} بازی.\n"
                    "آمار ردیف‌های جدول در بخش «تیم‌ها → آمار وارداتی» دیده می‌شود.")

    # ---------------- عمومی ----------------
    def refresh_all(self):
        self._refresh_table()
        self._refresh_teams()
        self._refresh_matches()
        names = [t["name"] for t in data.list_teams()]
        for menu in (getattr(self, "home_menu", None), getattr(self, "away_menu", None),
                     getattr(self, "ph_home_menu", None), getattr(self, "ph_away_menu", None)):
            if menu:
                menu.configure(values=names)


# ======================= پنجرهٔ جزئیات تیم =======================
RESULT_FA = {"W": "برد", "D": "مساوی", "L": "باخت"}


class TeamDetailWindow(ctk.CTkToplevel):
    def __init__(self, master, team_id):
        super().__init__(master)
        self.master_app = master
        self.team_id = team_id
        t = data.get_team(team_id)
        self.title(f"جزئیات تیم {t['name']}")
        self.geometry("980x700")
        self.transient(master)
        self.grab_set()
        self._build(t)
        try:
            apply_rtl(self)
        except Exception:
            pass

    def _build(self, t):
        head = ctk.CTkFrame(self, fg_color=t["color"] or "#2c7be5", corner_radius=0)
        head.pack(fill="x")
        ctk.CTkLabel(head, text=f"🛡 {t['name']}", font=(FONT, 26, "bold"),
                     text_color="white").pack(side="right", padx=16, pady=12)
        info = f"شهر: {t['city'] or '-'}    |    ورزشگاه: {t['stadium'] or '-'}    |    سرمربی: {t['coach'] or '-'}"
        ctk.CTkLabel(head, text=info, font=(FONT, 14), text_color="white").pack(side="right", padx=10)

        tabs = ctk.CTkTabview(self, anchor="e")
        tabs.pack(fill="both", expand=True, padx=10, pady=10)
        tb_over = tabs.add("نمای کلی")
        tb_news = tabs.add("اخبار")
        tb_played = tabs.add("بازی‌های اخیر")
        tb_next = tabs.add("بازی‌های پیش‌رو")
        tb_players = tabs.add("بازیکنان")

        s = data.team_stats(self.team_id)
        self._overview(tb_over, s)
        self._news(tb_news)
        self._recent(tb_played, s)
        self._upcoming(tb_next, s)
        self._players(tb_players, s)

    # ---- نمای کلی ----
    def _overview(self, frame, s):
        st = s["stats"] or {}
        grid = ctk.CTkFrame(frame, fg_color="transparent")
        grid.pack(fill="x", padx=14, pady=14)
        cards = [("رتبه در جدول", str(st.get("rank", "-"))),
                 ("امتیاز", str(st.get("pts", 0))),
                 ("بازی انجام‌شده", str(st.get("played", 0))),
                 ("برد / مساوی / باخت", f"{st.get('w',0)} / {st.get('d',0)} / {st.get('l',0)}"),
                 ("گل زده / خورده", f"{st.get('gf',0)} / {st.get('ga',0)}"),
                 ("تفاضل گل", str(st.get("gd", 0)))]
        for i, (title, val) in enumerate(cards):
            c = ctk.CTkFrame(grid, fg_color="#1b2233", corner_radius=10)
            c.grid(row=i // 3, column=i % 3, padx=8, pady=8, sticky="nsew")
            grid.grid_columnconfigure(i % 3, weight=1)
            ctk.CTkLabel(c, text=title, font=(FONT, 12), text_color="gray").pack(pady=(10, 2))
            ctk.CTkLabel(c, text=val, font=(FONT, 20, "bold")).pack(pady=(0, 10))

        # نوار قدرت
        pw = ctk.CTkFrame(frame, fg_color="#1b2233", corner_radius=10)
        pw.pack(fill="x", padx=14, pady=6)
        ctk.CTkLabel(pw, text=f"⚡ قدرت تیم: {s['power']:.0f} از ۱۰۰ "
                              f"(میانگین امتیاز بازیکنان: {s['avg_rating'] or '-'})",
                     font=(FONT, 14, "bold")).pack(anchor="e", padx=12, pady=(10, 2))
        bar = ctk.CTkProgressBar(pw, height=16)
        bar.set(s["power"] / 100.0)
        bar.pack(fill="x", padx=12, pady=(0, 12))

        # آمار وارداتی از OCR (اگر وجود داشت)
        for season in set([data.get_setting("season", "")] + data.seasons()):
            raw = data.get_setting(f"rowstats:{self.team_id}:{season or ''}")
            if raw:
                keys = ("بازی", "برد", "تساوی", "باخت", "GF", "GA", "GD", "PTS")
                vals = [(k + ": " + (v or "-")) for k, v in zip(keys, raw.split(";"))]
                ctk.CTkLabel(frame, text=f"📥 آمار وارداتی فصل {season or '-'}:  " + " | ".join(vals),
                             font=(FONT, 12), text_color="#9aa5c0").pack(anchor="e", padx=16, pady=2)

        # فرم
        form = st.get("form", [])
        if form:
            ftxt = "فرم ۵ بازی اخیر:  " + "  ".join(
                f"{RESULT_FA[x]}({'✅' if x=='W' else '❌' if x=='L' else '➖'})" for x in reversed(form))
            ctk.CTkLabel(frame, text=ftxt, font=(FONT, 13)).pack(anchor="e", padx=16, pady=6)

    # ---- اخبار ----
    def _news(self, frame):
        top = ctk.CTkFrame(frame, fg_color="transparent"); top.pack(fill="x", padx=10, pady=8)
        title_e = ctk.CTkEntry(top, font=(FONT, 13), placeholder_text=" تیتر خبر")
        title_e.pack(side="right", fill="x", expand=True, padx=6)
        body_e = ctk.CTkEntry(top, font=(FONT, 13), placeholder_text="متن خبر (اختیاری)")
        body_e.pack(side="right", fill="x", expand=True, padx=6)
        def add():
            if not title_e.get().strip():
                return
            data.add_news(self.team_id, title_e.get(), body_e.get())
            title_e.delete(0, "end"); body_e.delete(0, "end")
            self._refresh_news(frame)
        ctk.CTkButton(top, text="➕ افزودن خبر", width=110, command=add).pack(side="right")
        self.news_box = ctk.CTkScrollableFrame(frame, fg_color="#151a28")
        self.news_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._refresh_news(frame)

    def _refresh_news(self, frame):
        for w in self.news_box.winfo_children():
            w.destroy()
        news = data.list_news(self.team_id)
        if not news:
            ctk.CTkLabel(self.news_box, text="خبری ثبت نشده — اولین خبر را بالا اضافه کنید.",
                         font=(FONT, 13), text_color="gray").pack(pady=24)
            return
        for n in news:
            card = ctk.CTkFrame(self.news_box, fg_color="#1b2233", corner_radius=8)
            card.pack(fill="x", padx=6, pady=4)
            txt = f"🗞 {n['title']}   ({n['date']})"
            if n["body"]:
                txt += f"\n{n['body']}"
            ctk.CTkLabel(card, text=txt, font=(FONT, 13), justify="right",
                         wraplength=780).pack(side="right", padx=10, pady=8, anchor="ne")
            ctk.CTkButton(card, text="🗑", width=36, fg_color="#8b2e3b",
                          command=lambda nid=n["id"]: (data.delete_news(nid), self._refresh_news(frame)))\
                .pack(side="left", padx=6)

    # ---- بازی‌های اخیر ----
    def _recent(self, frame, s):
        box = ctk.CTkScrollableFrame(frame, fg_color="#151a28")
        box.pack(fill="both", expand=True, padx=10, pady=10)
        if not s["recent"]:
            ctk.CTkLabel(box, text="بازی انجام‌شده‌ای ثبت نشده است.",
                         font=(FONT, 14), text_color="gray").pack(pady=30)
            return
        for r in reversed(s["recent"]):
            m = r["match"]
            col = "#2ecc71" if r["result"] == "W" else "#e74c3c" if r["result"] == "L" else "#f1c40f"
            row = ctk.CTkFrame(box, fg_color="#1b2233", corner_radius=8)
            row.pack(fill="x", padx=6, pady=4)
            badge = ctk.CTkLabel(row, text=RESULT_FA[r["result"]], font=(FONT, 14, "bold"),
                                 text_color="white", fg_color=col, corner_radius=8, width=64)
            badge.pack(side="right", padx=10, pady=10)
            txt = f"{m['home_name']} {m['home_goals']} - {m['away_goals']} {m['away_name']}"
            extra = f"   |   تاریخ: {m['date'] or '-'}   هفته: {m['week'] or '-'}"
            ctk.CTkLabel(row, text=txt + extra, font=(FONT, 14)).pack(side="right", padx=6)

    # ---- پیش‌رو ----
    def _upcoming(self, frame, s):
        box = ctk.CTkScrollableFrame(frame, fg_color="#151a28")
        box.pack(fill="both", expand=True, padx=10, pady=10)
        if not s["upcoming"]:
            ctk.CTkLabel(box, text="بازی پیش‌رویی ثبت نشده است.",
                         font=(FONT, 14), text_color="gray").pack(pady=30)
            return
        for m in s["upcoming"]:
            row = ctk.CTkFrame(box, fg_color="#1b2233", corner_radius=8)
            row.pack(fill="x", padx=6, pady=4)
            opp = m["away_name"] if m["home_id"] == self.team_id else m["home_name"]
            where = "میزبان 🏟" if m["home_id"] == self.team_id else "میهمان ✈"
            p = data.predict_match(m["home_id"], m["away_id"])
            txt = (f"📅 {m['date'] or '---'}   هفته {m['week'] or '-'}   {where}   مقابل {opp}\n"
                   f"پیش‌بینی مدل: {p['score']}  (برد {p['p_home']*100:.0f}% / مساوی {p['p_draw']*100:.0f}% / "
                   f"باخت {p['p_away']*100:.0f}%)")
            ctk.CTkLabel(row, text=txt, font=(FONT, 13), justify="right",
                         wraplength=800).pack(side="right", padx=12, pady=8)

    # ---- بازیکنان ----
    def _players(self, frame, s):
        top = ctk.CTkFrame(frame, fg_color="transparent"); top.pack(fill="x", padx=10, pady=(8, 2))
        ctk.CTkLabel(top, text="افزودن بازیکن:", font=(FONT, 13, "bold")).pack(side="right")
        name_e = ctk.CTkEntry(top, width=170, font=(FONT, 13), placeholder_text="نام")
        name_e.pack(side="right", padx=5)
        pos_v = ctk.StringVar(value="FW")
        pos_m = ctk.CTkOptionMenu(top, variable=pos_v, values=data.POS_ORDER, width=110)
        pos_m.pack(side="right", padx=5)
        num_e = ctk.CTkEntry(top, width=60, font=(FONT, 13), placeholder_text="پیراهن")
        num_e.pack(side="right", padx=5)
        rat_e = ctk.CTkEntry(top, width=60, font=(FONT, 13), placeholder_text="امتیاز")
        rat_e.pack(side="right", padx=5)
        g_e = ctk.CTkEntry(top, width=52, font=(FONT, 13), placeholder_text="گل")
        g_e.pack(side="right", padx=5)
        a_e = ctk.CTkEntry(top, width=52, font=(FONT, 13), placeholder_text="پاس گل")
        a_e.pack(side="right", padx=5)

        def add():
            if not name_e.get().strip():
                return
            def i(v, d=0):
                v = v.get().strip()
                return int(v) if v.isdigit() else d
            try:
                data.add_player(self.team_id, name_e.get(), pos_v.get(), i(num_e), 0, "",
                                i(g_e), i(a_e), float(i(rat_e, 60) or 60))
            except Exception as e:
                messagebox.showerror("خطا", str(e), parent=self)
                return
            name_e.delete(0, "end")
            self.master_app.refresh_all()
            self.destroy()
            TeamDetailWindow(self.master_app, self.team_id)
        ctk.CTkButton(top, text="➕", width=44, command=add).pack(side="right", padx=4)

        box = ctk.CTkScrollableFrame(frame, fg_color="#151a28")
        box.pack(fill="both", expand=True, padx=10, pady=8)
        players = s["players"]
        if not players:
            ctk.CTkLabel(box, text="بازیکنی ثبت نشده — با فرم بالا اضافه کنید.",
                         font=(FONT, 14), text_color="gray").pack(pady=30)
            return
        for p in players:
            row = ctk.CTkFrame(box, fg_color="#1b2233", corner_radius=8)
            row.pack(fill="x", padx=6, pady=3)
            txt = (f"#{p['jersey'] or '-':>2}  {p['name']}   "
                   f"({data.POS_FA.get(p['position'], p['position'])})   "
                   f"⚽ {p['goals']}   🅰 {p['assists']}   امتیاز {p['rating']:.0f}")
            ctk.CTkLabel(row, text=txt, font=(FONT, 13)).pack(side="right", padx=10, pady=7)
            ctk.CTkButton(row, text="🗑", width=36, fg_color="#8b2e3b",
                          command=lambda pid=p["id"]: self._del_player(pid))\
                .pack(side="left", padx=6)

    def _del_player(self, pid):
        data.delete_player(pid)
        self.master_app.refresh_all()
        self.destroy()
        TeamDetailWindow(self.master_app, self.team_id)
