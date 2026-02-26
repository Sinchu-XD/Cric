import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= CONFIG =================
API_ID = 35362137
API_HASH = "c3c3e167ea09bc85369ca2fa3c1be790"
BOT_TOKEN = "8490783791:AAFT8DygQAO5cC-Bg6yi_D-0c7wOlIKDFdA"
RAPID_API_KEY = "1bf70049e7msh71db390a6f430e7p125822jsnb7c6630377f7"

# ================= API =================

class CricbuzzAPI:
    BASE_URL = "https://cricbuzz-cricket2.p.rapidapi.com"

    def __init__(self, key):
        self.headers = {
            "x-rapidapi-key": key,
            "x-rapidapi-host": "cricbuzz-cricket2.p.rapidapi.com"
        }

    def _get(self, endpoint):
        r = requests.get(f"{self.BASE_URL}{endpoint}",
                         headers=self.headers,
                         timeout=10)
        r.raise_for_status()
        return r.json()

    def _extract(self, data):
        matches = []
        for t in data.get("typeMatches", []):
            for s in t.get("seriesMatches", []):
                wrap = s.get("seriesAdWrapper", {})
                for m in wrap.get("matches", []):
                    info = m.get("matchInfo", {})
                    matches.append({
                        "id": info.get("matchId"),
                        "team1": info.get("team1", {}).get("teamName"),
                        "team2": info.get("team2", {}).get("teamName"),
                        "status": info.get("status"),
                        "state": info.get("state")
                    })
        return matches

    def live(self):
        return [m for m in self._extract(self._get("/matches/v1/live"))
                if m["state"] not in ["Complete", "Preview"]]

    def recent(self):
        return [m for m in self._extract(self._get("/matches/v1/recent"))
                if m["state"] == "Complete"]

    def upcoming(self):
        return [m for m in self._extract(self._get("/matches/v1/upcoming"))
                if m["state"] == "Preview"]

    def scorecard(self, match_id):
        return self._get(f"/mcenter/v1/{match_id}/scard")

    def squads(self, match_id):
        return self._get(f"/mcenter/v1/{match_id}/teams")

    def commentary(self, match_id):
        return self._get(f"/mcenter/v1/{match_id}/leanback")


api = CricbuzzAPI(RAPID_API_KEY)
app = Client("cricket_bot", bot_token=BOT_TOKEN,
             api_id=API_ID, api_hash=API_HASH)

# ================= MENUS =================

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔴 Live Matches", callback_data="live")],
        [InlineKeyboardButton("🔵 Recent Matches", callback_data="recent")],
        [InlineKeyboardButton("🟢 Upcoming Matches", callback_data="upcoming")]
    ])

def back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="back")]])

def detail_menu(mid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Scorecard", callback_data=f"score_{mid}")],
        [InlineKeyboardButton("👥 Squads", callback_data=f"squad_{mid}")],
        [InlineKeyboardButton("🔴 Live Status", callback_data=f"live_{mid}")],
        [InlineKeyboardButton("⬅ Back", callback_data="back")]
    ])

# ================= FORMATTERS =================

def format_scorecard(data):
    if "scorecard" not in data:
        return "No scorecard available."

    text = "📊 FULL SCORECARD\n"
    text += "="*80 + "\n"

    for inn in data["scorecard"]:
        text += f"🏏 {inn['batteamname']} - {inn['score']}/{inn['wickets']} ({inn['overs']} overs)\n"
        text += "-"*80 + "\n"
        text += "BATTING:\n"
        text += f"{'Player':25} {'R':>4} {'B':>4} {'4s':>4} {'6s':>4} {'SR':>6}\n"
        text += "-"*80 + "\n"

        for b in inn["batsman"]:
            text += f"{b['name'][:25]:25} {b['runs']:>4} {b['balls']:>4} {b['fours']:>4} {b['sixes']:>4} {b['strkrate']:>6}\n"

        text += "\nBOWLING:\n"
        text += f"{'Bowler':25} {'O':>4} {'M':>4} {'R':>4} {'W':>4} {'Eco':>6}\n"
        text += "-"*80 + "\n"

        for bw in inn["bowler"]:
            text += f"{bw['name'][:25]:25} {bw['overs']:>4} {bw['maidens']:>4} {bw['runs']:>4} {bw['wickets']:>4} {bw['economy']:>6}\n"

        text += "\n"

    return text[:4096]

def format_squads(data):
    text = "👥 SQUADS\n"
    text += "="*80 + "\n"

    for tk in ["team1", "team2"]:
        team = data[tk]["team"]["teamname"]
        text += f"🏏 {team}\n"
        text += "-"*50 + "\n"

        for grp in data[tk]["players"]:
            text += f"{grp['category'].upper()}:\n"
            for p in grp["player"]:
                cap = " (C)" if p["captain"] else ""
                wk = " (WK)" if p["keeper"] else ""
                text += f"- {p['name']}{cap}{wk} - {p['role']}\n"
            text += "\n"

    return text[:4096]

def format_live(data):
    mini = data.get("miniscore")
    header = data.get("matchheaders", {})
    if not mini:
        return "No live data."

    text = "🔴 LIVE STATUS\n"
    text += "="*80 + "\n"
    text += f"Status : {header.get('status')}\n"
    text += f"Score  : {mini['batteamscore']['teamscore']}/{mini['batteamscore']['teamwkts']}\n"
    text += f"Run Rate : {mini.get('crr')}\n\n"

    text += f"Striker      : {mini['batsmanstriker']['name']} {mini['batsmanstriker']['runs']}({mini['batsmanstriker']['balls']})\n"
    text += f"Non-Striker  : {mini['batsmannonstriker']['name']} {mini['batsmannonstriker']['runs']}({mini['batsmannonstriker']['balls']})\n"
    text += f"Bowler       : {mini['bowlerstriker']['name']} {mini['bowlerstriker']['overs']} overs\n"

    return text[:4096]

# ================= START =================

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("🏏 ABHI CRICKET BOT\n\nSelect Option:",
                             reply_markup=main_menu())

# ================= CALLBACK =================

@app.on_callback_query()
async def cb(client, query):
    d = query.data

    if d == "back":
        await query.message.edit_text("🏏 ABHI CRICKET BOT\n\nSelect Option:",
                                      reply_markup=main_menu())
        return

    if d in ["live", "recent", "upcoming"]:
        matches = getattr(api, d)()[:10]
        buttons = []
        text = f"{d.upper()} MATCHES\n\n"

        for m in matches:
            text += f"{m['team1']} vs {m['team2']}\n{m['status']}\n\n"
            buttons.append([InlineKeyboardButton(
                f"{m['team1']} vs {m['team2']}",
                callback_data=f"match_{m['id']}"
            )])

        buttons.append([InlineKeyboardButton("⬅ Back", callback_data="back")])

        await query.message.edit_text(text,
                                      reply_markup=InlineKeyboardMarkup(buttons))
        return

    if d.startswith("match_"):
        mid = d.split("_")[1]
        await query.message.edit_text("Select Match Details:",
                                      reply_markup=detail_menu(mid))
        return

    if d.startswith("score_"):
        mid = d.split("_")[1]
        await query.message.edit_text(format_scorecard(api.scorecard(mid)),
                                      reply_markup=detail_menu(mid))
        return

    if d.startswith("squad_"):
        mid = d.split("_")[1]
        await query.message.edit_text(format_squads(api.squads(mid)),
                                      reply_markup=detail_menu(mid))
        return

    if d.startswith("live_"):
        mid = d.split("_")[1]
        await query.message.edit_text(format_live(api.commentary(mid)),
                                      reply_markup=detail_menu(mid))
        return

# ================= RUN =================
app.run()
