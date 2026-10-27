# -*- coding: utf-8 -*-
"""
لایهٔ دادهٔ جدول لیگ برتر ایران
- ذخیره‌سازی در SQLite (برای استفادهٔ بعدی در پیش‌بینی)
- محاسبهٔ رتبه‌بندی، آمار تیم و امتیاز قدرت (Power Rating)
- مدل‌های آماری برای پیش‌بینی نتایج
"""

import json
import math
import os
import sqlite3
import threading
from datetime import datetime

DB_DIR = os.path.join(os.path.expanduser("~"), "LeaguePro")
DB_PATH = os.path.join(DB_DIR, "league.db")

_lock = threading.Lock()

POS_ORDER = ["GK", "DF", "MF", "FW"]
POS_FA = {"GK": "دروازه‌بان", "DF": "مدافع", "MF": "هافبک", "FW": "مهاجم"}


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def _conn():
    os.makedirs(DB_DIR, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


SCHEMA = """
CREATE TABLE IF NOT EXISTS teams(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    city TEXT DEFAULT '',
    stadium TEXT DEFAULT '',
    coach TEXT DEFAULT '',
    color TEXT DEFAULT '#2c7be5',
    logo_path TEXT DEFAULT '',
    power REAL DEFAULT 50.0,
    created_at TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS players(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    position TEXT DEFAULT 'MF',
    jersey INTEGER DEFAULT 0,
    age INTEGER DEFAULT 0,
    nationality TEXT DEFAULT '',
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    rating REAL DEFAULT 60.0
);
CREATE TABLE IF NOT EXISTS matches(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season TEXT DEFAULT '',
    week INTEGER DEFAULT 0,
    date TEXT DEFAULT '',
    home_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    away_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    home_goals INTEGER DEFAULT NULL,
    away_goals INTEGER DEFAULT NULL,
    status TEXT DEFAULT 'scheduled',
    venue TEXT DEFAULT '',
    source TEXT DEFAULT 'manual'
);
CREATE TABLE IF NOT EXISTS news(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    body TEXT DEFAULT '',
    date TEXT DEFAULT '',
    url TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
"""


def init_db():
    with _lock:
        c = _conn()
        c.executescript(SCHEMA)
        c.commit()
        c.close()


# ---------------- تنظیمات ----------------
def get_setting(key, default=None):
    try:
        with _lock:
            c = _conn()
            r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            c.close()
        return r["value"] if r else default
    except Exception:
        return default


def set_setting(key, value):
    with _lock:
        c = _conn()
        c.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                  "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
        c.commit()
        c.close()


# ---------------- CRUD ----------------
def list_teams():
    with _lock:
        c = _conn()
        rows = [dict(r) for r in c.execute("SELECT * FROM teams ORDER BY name COLLATE NOCASE").fetchall()]
        c.close()
    return rows


def get_team(team_id):
    with _lock:
        c = _conn()
        r = c.execute("SELECT * FROM teams WHERE id=?", (team_id,)).fetchone()
        c.close()
    return dict(r) if r else None


def find_team_by_name(name):
    name = (name or "").strip()
    if not name:
        return None
    for t in list_teams():
        if t["name"].strip() == name:
            return t
    for t in list_teams():
        if name in t["name"] or t["name"] in name:
            return t
    return None


def add_team(name, city="", stadium="", coach="", color="#2c7be5"):
    name = (name or "").strip()
    if not name:
        raise ValueError("نام تیم نمی‌تواند خالی باشد")
    with _lock:
        c = _conn()
        try:
            cur = c.execute(
                "INSERT INTO teams(name,city,stadium,coach,color,created_at) VALUES(?,?,?,?,?,?)",
                (name, city.strip(), stadium.strip(), coach.strip(), color, now_iso()))
            c.commit()
            tid = cur.lastrowid
        finally:
            c.close()
    recompute_power_all()
    return tid


def update_team(team_id, **kw):
    fields = ["name", "city", "stadium", "coach", "color", "logo_path", "power"]
    sets = {k: kw[k] for k in fields if k in kw}
    if not sets:
        return
    with _lock:
        c = _conn()
        c.execute("UPDATE teams SET " + ",".join(f"{k}=?" for k in sets) + " WHERE id=?",
                  (*sets.values(), team_id))
        c.commit()
        c.close()


def delete_team(team_id):
    with _lock:
        c = _conn()
        c.execute("DELETE FROM teams WHERE id=?", (team_id,))
        c.commit()
        c.close()


def list_players(team_id=None):
    with _lock:
        c = _conn()
        if team_id:
            rows = [dict(r) for r in c.execute(
                "SELECT * FROM players WHERE team_id=? ORDER BY "
                "CASE position WHEN 'GK' THEN 0 WHEN 'DF' THEN 1 WHEN 'MF' THEN 2 ELSE 3 END, jersey",
                (team_id,)).fetchall()]
        else:
            rows = [dict(r) for r in c.execute("SELECT * FROM players ORDER BY team_id").fetchall()]
        c.close()
    return rows


def add_player(team_id, name, position="MF", jersey=0, age=0, nationality="",
               goals=0, assists=0, rating=60.0):
    with _lock:
        c = _conn()
        cur = c.execute(
            "INSERT INTO players(team_id,name,position,jersey,age,nationality,goals,assists,rating) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (team_id, name.strip(), position, jersey, age, nationality, goals, assists, rating))
        c.commit()
        pid = cur.lastrowid
        c.close()
    recompute_power_all()
    return pid


def update_player(pid, **kw):
    fields = ["name", "position", "jersey", "age", "nationality", "goals", "assists", "rating", "team_id"]
    sets = {k: kw[k] for k in fields if k in kw}
    if not sets:
        return
    with _lock:
        c = _conn()
        c.execute("UPDATE players SET " + ",".join(f"{k}=?" for k in sets) + " WHERE id=?",
                  (*sets.values(), pid))
        c.commit()
        c.close()
    recompute_power_all()


def delete_player(pid):
    with _lock:
        c = _conn()
        c.execute("DELETE FROM players WHERE id=?", (pid,))
        c.commit()
        c.close()
    recompute_power_all()


def list_matches(season=None, upcoming_only=False, past_only=False, limit=None):
    q = ("SELECT m.*, ht.name AS home_name, ht.color AS home_color, "
         "at.name AS away_name, at.color AS away_color "
         "FROM matches m JOIN teams ht ON ht.id=m.home_id JOIN teams at ON at.id=m.away_id WHERE 1=1")
    args = []
    if season:
        q += " AND m.season=?"
        args.append(season)
    if upcoming_only:
        q += " AND m.status='scheduled'"
    if past_only:
        q += " AND m.status<>'scheduled'"
    q += " ORDER BY CASE m.status WHEN 'scheduled' THEN 0 ELSE 1 END, m.date, m.week"
    if limit:
        q += f" LIMIT {int(limit)}"
    with _lock:
        c = _conn()
        rows = [dict(r) for r in c.execute(q, args).fetchall()]
        c.close()
    return rows


def add_match(home_id, away_id, date="", week=0, home_goals=None, away_goals=None,
              season="", venue="", source="manual"):
    if home_id == away_id:
        raise ValueError("دو تیم یکسان نمی‌توانند با هم بازی کنند")
    status = "finished" if (home_goals is not None and away_goals is not None) else "scheduled"
    with _lock:
        c = _conn()
        cur = c.execute(
            "INSERT INTO matches(season,week,date,home_id,away_id,home_goals,away_goals,status,venue,source) "
            "VALUES(?,?,?,?,?,?,?,?,?,?)",
            (season, week, date, home_id, away_id, home_goals, away_goals, status, venue, source))
        c.commit()
        mid = cur.lastrowid
        c.close()
    recompute_power_all()
    return mid


def update_match(mid, **kw):
    fields = ["season", "week", "date", "home_id", "away_id", "home_goals", "away_goals", "venue", "status"]
    sets = {k: kw[k] for k in fields if k in kw}
    if not sets:
        return
    if "home_goals" in sets or "away_goals" in sets:
        hg = sets.get("home_goals")
        ag = sets.get("away_goals")
        sets["status"] = "finished" if (hg is not None and ag is not None) else "scheduled"
    with _lock:
        c = _conn()
        c.execute("UPDATE matches SET " + ",".join(f"{k}=?" for k in sets) + " WHERE id=?",
                  (*sets.values(), mid))
        c.commit()
        c.close()
    recompute_power_all()


def delete_match(mid):
    with _lock:
        c = _conn()
        c.execute("DELETE FROM matches WHERE id=?", (mid,))
        c.commit()
        c.close()
    recompute_power_all()


def list_news(team_id=None):
    with _lock:
        c = _conn()
        if team_id:
            rows = [dict(r) for r in c.execute(
                "SELECT n.*, t.name AS team_name FROM news n JOIN teams t ON t.id=n.team_id "
                "WHERE n.team_id=? ORDER BY n.date DESC", (team_id,)).fetchall()]
        else:
            rows = [dict(r) for r in c.execute(
                "SELECT n.*, t.name FROM news n JOIN teams t ON t.id=n.team_id "
                "ORDER BY n.date DESC LIMIT 100").fetchall()]
        c.close()
    return rows


def add_news(team_id, title, body="", date="", url=""):
    with _lock:
        c = _conn()
        cur = c.execute("INSERT INTO news(team_id,title,body,date,url) VALUES(?,?,?,?,?)",
                        (team_id, title.strip(), body, date or now_iso()[:10], url))
        c.commit()
        nid = cur.lastrowid
        c.close()
    return nid


def delete_news(nid):
    with _lock:
        c = _conn()
        c.execute("DELETE FROM news WHERE id=?", (nid,))
        c.commit()
        c.close()


def seasons():
    with _lock:
        c = _conn()
        rows = [r["season"] for r in c.execute(
            "SELECT DISTINCT season FROM matches WHERE season<>'' ORDER BY season DESC").fetchall()]
        c.close()
    return rows


# ---------------- جدول و آمار ----------------
def standings(season=None):
    """محاسبهٔ جدول از نتایج; اگر بازی انجام‌شده‌ای نباشد، ستون‌ها صفر می‌مانند."""
    teams = {t["id"]: dict(t, played=0, w=0, d=0, l=0, gf=0, ga=0, gd=0, pts=0, form=[])
             for t in list_teams()}
    matches = sorted(list_matches(season=season, past_only=True), key=lambda m: (m["date"], m["week"] or 0))
    for m in matches:
        h, a = teams.get(m["home_id"]), teams.get(m["away_id"])
        if not h or not a or m["home_goals"] is None or m["away_goals"] is None:
            continue
        hg, ag = int(m["home_goals"]), int(m["away_goals"])
        h["played"] += 1; a["played"] += 1
        h["gf"] += hg; h["ga"] += ag; a["gf"] += ag; a["ga"] += hg
        h["gd"] = h["gf"] - h["ga"]; a["gd"] = a["gf"] - a["ga"]
        if hg > ag:
            h["w"] += 1; a["l"] += 1; h["pts"] += 3
            h["form"].append("W"); a["form"].append("L")
        elif hg < ag:
            a["w"] += 1; h["l"] += 1; a["pts"] += 3
            h["form"].append("L"); a["form"].append("W")
        else:
            h["d"] += 1; a["d"] += 1; h["pts"] += 1; a["pts"] += 1
            h["form"].append("D"); a["form"].append("D")
    table = sorted(teams.values(), key=lambda t: (-t["pts"], -t["gd"], -t["gf"], t["name"]))
    for i, t in enumerate(table):
        t["rank"] = i + 1
        t["form"] = t["form"][-5:]
    return table


def team_stats(team_id, last_n=5):
    t = get_team(team_id)
    if not t:
        return None
    st = {x["id"]: x for x in standings()}
    s = st.get(team_id, {})
    finished = [m for m in list_matches(past_only=True)
                if m["home_id"] == team_id or m["away_id"] == team_id]
    finished.sort(key=lambda m: (m["date"], m["week"] or 0))
    recent = []
    for m in finished[-last_n:]:
        hg, ag = int(m["home_goals"] or 0), int(m["away_goals"] or 0)
        mine, opp = (hg, ag) if m["home_id"] == team_id else (ag, hg)
        recent.append(dict(match=m, result=("W" if mine > opp else "L" if mine < opp else "D"),
                           scored=mine, conceded=opp))
    upcoming = [m for m in list_matches(upcoming_only=True)
                if m["home_id"] == team_id or m["away_id"] == team_id][:last_n]
    players = list_players(team_id)
    avg_rating = round(sum(p["rating"] for p in players) / len(players), 1) if players else 0
    top_scorers = sorted(players, key=lambda p: -p["goals"])[:5]
    return dict(team=t, stats=s, recent=recent, upcoming=upcoming,
                players=players, avg_rating=avg_rating, top_scorers=top_scorers,
                power=t["power"])


# ---------------- قدرت تیم ----------------
def recompute_power(team_id):
    """امتیاز قدرت ۰..۱۰۰ : ترکیب میانگین امتیاز بازیکنان + عملکرد جدولی"""
    t = get_team(team_id)
    if not t:
        return
    players = list_players(team_id)
    pos_w = {"GK": 1.0, "DF": 0.95, "MF": 1.0, "FW": 1.05}
    if players:
        tot = sum(p["rating"] * pos_w.get(p["position"], 1.0) for p in players)
        cnt = sum(pos_w.get(p["position"], 1.0) for p in players) or 1
        squad = tot / cnt  # 0..100
    else:
        squad = 50.0
    table = {x["id"]: x for x in standings()}
    s = table.get(team_id)
    if s and s["played"] >= 3:
        perf = min(100.0, (s["pts"] / (3 * s["played"])) * 100)
        power = 0.55 * squad + 0.45 * perf
    else:
        power = squad
    power = round(max(0.0, min(100.0, power)), 1)
    update_team(team_id, power=power)
    return power


def recompute_power_all():
    for t in list_teams():
        recompute_power(t["id"])


# ---------------- پیش‌بینی ----------------
def _expected_goals(mu_h, mu_a, max_goals=10):
    """توزیع پواسون دو-متغیرهٔ مستقل -> ماتریس احتمال نتیجه"""
    ph = [math.exp(-mu_h) * mu_h ** k / math.factorial(k) for k in range(max_goals + 1)]
    pa = [math.exp(-mu_a) * mu_a ** k / math.factorial(k) for k in range(max_goals + 1)]
    return [[ph[i] * pa[j] for j in range(max_goals + 1)] for i in range(max_goals + 1)]


def predict_match(home_id, away_id, season=None):
    """پیش‌بینی مبتنی بر پواسون: گل‌انتظار از نرخ حمله/دفاع هر تیم + ضریب میزبانی و قدرت"""
    table = {x["id"]: x for x in standings(season=season)}
    league_avg = 1.35
    home_adv = 1.15
    H, A = table.get(home_id), table.get(away_id)
    if H and A and H["played"] >= 2 and A["played"] >= 2:
        att_h = max(0.2, H["gf"] / H["played"] / league_avg)
        def_h = max(0.2, H["ga"] / H["played"] / league_avg)
        att_a = max(0.2, A["gf"] / A["played"] / league_avg)
        def_a = max(0.2, A["ga"] / A["played"] / league_avg)
        base = league_avg
    else:
        th = get_team(home_id) or {"power": 50}
        ta = get_team(away_id) or {"power": 50}
        diff = (th["power"] - ta["power"]) / 100.0
        att_h = max(0.3, min(2.5, 1 + diff))
        def_a = max(0.3, min(2.5, 1 - diff))
        att_a = max(0.3, min(2.5, 1 - diff))
        def_h = max(0.3, min(2.5, 1 + diff))
        base = league_avg
    mu_h = max(0.05, base * att_h * def_a * home_adv)
    mu_a = max(0.05, base * att_a * def_h)
    mat = _expected_goals(mu_h, mu_a)
    n = len(mat)
    p_home = sum(mat[i][j] for i in range(n) for j in range(n) if i > j)
    p_draw = sum(mat[i][j] for i in range(n) for j in range(n) if i == j)
    p_away = sum(mat[i][j] for i in range(n) for j in range(n) if i < j)
    best = max(((mat[i][j], i, j) for i in range(n) for j in range(n)), key=lambda x: x[0])
    return dict(mu_home=round(mu_h, 2), mu_away=round(mu_a, 2),
                p_home=round(p_home, 3), p_draw=round(p_draw, 3), p_away=round(p_away, 3),
                score=f"{best[1]}-{best[2]}", score_prob=round(best[0], 3))


def export_backup(path):
    with _lock:
        c = _conn()
        data = {}
        for tbl in ("teams", "players", "matches", "news", "settings"):
            data[tbl] = [dict(r) for r in c.execute(f"SELECT * FROM {tbl}").fetchall()]
        c.close()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def import_backup(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    with _lock:
        c = _conn()
        c.executescript(SCHEMA)
        for tbl in ("news", "matches", "players", "teams", "settings"):
            c.execute(f"DELETE FROM {tbl}")
        for row in data.get("teams", []):
            c.execute("INSERT INTO teams(id,name,city,stadium,coach,color,logo_path,power,created_at) "
                      "VALUES(:id,:name,:city,:stadium,:coach,:color,:logo_path,:power,:created_at)", row)
        for row in data.get("players", []):
            c.execute("INSERT INTO players(id,team_id,name,position,jersey,age,nationality,goals,assists,rating) "
                      "VALUES(:id,:team_id,:name,:position,:jersey,:age,:nationality,:goals,:assists,:rating)", row)
        for row in data.get("matches", []):
            c.execute("INSERT INTO matches(id,season,week,date,home_id,away_id,home_goals,away_goals,status,venue,source) "
                      "VALUES(:id,:season,:week,:date,:home_id,:away_id,:home_goals,:away_goals,:status,:venue,:source)", row)
        for row in data.get("news", []):
            c.execute("INSERT INTO news(id,team_id,title,body,date,url) VALUES(:id,:team_id,:title,:body,:date,:url)", row)
        for row in data.get("settings", []):
            c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(:key,:value)", row)
        c.commit()
        c.close()
    recompute_power_all()
