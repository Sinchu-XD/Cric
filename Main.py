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

    text = "<b>📊 FULL SCORECARD</b>\n"
    text += "<pre>"

    for inn in data["scorecard"]:
        text += "=" * 60 + "\n"
        text += f"{inn['batteamname']} - {inn['score']}/{inn['wickets']} ({inn['overs']} ov)\n"
        text += "-" * 60 + "\n"

        # Batting Header
        text += f"{'Player':20} {'R':>3} {'B':>3} {'4s':>3} {'6s':>3} {'SR':>6}\n"
        text += "-" * 60 + "\n"

        for b in inn["batsman"]:
            name = b['name'][:20]
            text += f"{name:20} {b['runs']:>3} {b['balls']:>3} {b['fours']:>3} {b['sixes']:>3} {b['strkrate']:>6}\n"

        text += "\n"

        # Bowling Header
        text += f"{'Bowler':20} {'O':>4} {'M':>3} {'R':>3} {'W':>3} {'Eco':>6}\n"
        text += "-" * 60 + "\n"

        for bw in inn["bowler"]:
            name = bw['name'][:20]
            text += f"{name:20} {bw['overs']:>4} {bw['maidens']:>3} {bw['runs']:>3} {bw['wickets']:>3} {bw['economy']:>6}\n"

        text += "\n"

    text += "</pre>"
    return text

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

    try:

        # ================= BACK =================
        if d == "back":
            await query.message.edit_text(
                "🏏 <b>ABHI CRICKET BOT</b>\n\nSelect Option:",
                reply_markup=main_menu(),
                parse_mode="html"
            )
            return


        # ================= MATCH LIST =================
        if d in ["live", "recent", "upcoming"]:
            matches = getattr(api, d)()[:10]
            buttons = []

            title_map = {
                "live": "🔴 LIVE MATCHES",
                "recent": "🔵 RECENT MATCHES",
                "upcoming": "🟢 UPCOMING MATCHES"
            }

            text = f"<b>{title_map[d]}</b>\n\n"

            for m in matches:
                text += f"🏏 <b>{m['team1']} vs {m['team2']}</b>\n"
                text += f"Status: {m['status']}\n\n"

                buttons.append([
                    InlineKeyboardButton(
                        f"{m['team1']} vs {m['team2']}",
                        callback_data=f"match_{m['id']}"
                    )
                ])

            buttons.append([
                InlineKeyboardButton("⬅ Back", callback_data="back")
            ])

            await query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode="html"
            )
            return


        # ================= MATCH DETAILS MENU =================
        if d.startswith("match_"):
            mid = d.split("_")[1]

            await query.message.edit_text(
                "📂 <b>Select Match Details</b>",
                reply_markup=detail_menu(mid),
                parse_mode="html"
            )
            return


        # ================= SCORECARD =================
        if d.startswith("score_"):
            mid = d.split("_")[1]

            text = format_scorecard(api.scorecard(mid))

            await query.message.edit_text(
                text,
                reply_markup=detail_menu(mid),
                parse_mode="html",
                disable_web_page_preview=True
            )
            return


        # ================= SQUADS =================
        if d.startswith("squad_"):
            mid = d.split("_")[1]

            text = format_squads(api.squads(mid))

            await query.message.edit_text(
                text,
                reply_markup=detail_menu(mid),
                parse_mode="html"
            )
            return


        # ================= LIVE STATUS =================
        if d.startswith("live_"):
            mid = d.split("_")[1]

            text = format_live(api.commentary(mid))

            await query.message.edit_text(
                text,
                reply_markup=detail_menu(mid),
                parse_mode="html"
            )
            return


    except Exception as e:
        await query.message.edit_text(
            f"⚠ Error Occurred:\n<code>{e}</code>",
            parse_mode="html"
        )
# ================= RUN =================
app.run()
