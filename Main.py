import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode

# ================= CONFIG =================
API_ID = 35362137
API_HASH = "c3c3e167ea09bc85369ca2fa3c1be790"
BOT_TOKEN = "8490783791:AAFT8DygQAO5cC-Bg6yi_D-0c7wOlIKDFdA"
RAPID_API_KEY = "05f9848096mshc0acbed9073b9a1p16fea7jsnae5ab08f197e"

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
        [InlineKeyboardButton("🏏 Batting", callback_data=f"bat_{mid}")],
        [InlineKeyboardButton("🎯 Bowling", callback_data=f"bowl_{mid}")],
        [InlineKeyboardButton("📈 Strike Rate", callback_data=f"sr_{mid}")],
        [InlineKeyboardButton("👥 Squads", callback_data=f"squad_{mid}")],
        [InlineKeyboardButton("🔴 Live", callback_data=f"live_{mid}")],
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

        # Batting Header (NO SR)
        text += f"{'Player':22} {'R':>4} {'B':>4} {'4s':>4} {'6s':>4}\n"
        text += "-" * 60 + "\n"

        for b in inn["batsman"]:
            name = b['name'][:22]
            text += f"{name:22} {b['runs']:>4} {b['balls']:>4} {b['fours']:>4} {b['sixes']:>4}\n"

        text += "\n"

        # Bowling Header
        text += f"{'Bowler':22} {'O':>4} {'M':>4} {'R':>4} {'W':>4} {'Eco':>6}\n"
        text += "-" * 60 + "\n"

        for bw in inn["bowler"]:
            name = bw['name'][:22]
            text += f"{name:22} {bw['overs']:>4} {bw['maidens']:>4} {bw['runs']:>4} {bw['wickets']:>4} {bw['economy']:>6}\n"

        text += "\n"

    text += "</pre>"
    return text

def format_batting(data):
    if "scorecard" not in data:
        return "No data."

    text = "<b>🏏 BATTING SCORECARD</b>\n<pre>"

    for inn in data["scorecard"]:
        text += "="*42 + "\n"
        text += f"{inn['batteamname']}  {inn['score']}/{inn['wickets']}\n"
        text += "-"*42 + "\n"
        text += f"{'Player':16} {'R':>3} {'B':>3} {'4':>2} {'6':>2}\n"
        text += "-"*42 + "\n"

        for b in inn["batsman"]:
            name = b["name"][:16]
            text += f"{name:16} {b['runs']:>3} {b['balls']:>3} {b['fours']:>2} {b['sixes']:>2}\n"

        text += "\n"

    text += "</pre>"
    return text

def format_bowling(data):
    if "scorecard" not in data:
        return "No data."

    text = "<b>🎯 BOWLING SCORECARD</b>\n<pre>"

    for inn in data["scorecard"]:
        text += "="*45 + "\n"
        text += f"Bowling vs {inn['batteamname']}\n"
        text += "-"*45 + "\n"
        text += f"{'Bowler':16} {'O':>3} {'R':>3} {'W':>3} {'Eco':>5}\n"
        text += "-"*45 + "\n"

        for bw in inn["bowler"]:
            name = bw["name"][:16]
            eco = float(bw["economy"])
            text += f"{name:16} {bw['overs']:>3} {bw['runs']:>3} {bw['wickets']:>3} {eco:>5.1f}\n"

        text += "\n"

    text += "</pre>"
    return text


def format_strike_rate(data):
    if "scorecard" not in data:
        return "No data available."

    text = "<b>📈 STRIKE RATE DETAILS</b>\n"
    text += "<pre>"

    for inn in data["scorecard"]:
        text += "=" * 55 + "\n"
        text += f"{inn['batteamname']}\n"
        text += "-" * 55 + "\n"

        # Header (compact width to prevent wrap)
        text += f"{'Player':18} {'R':>4} {'B':>4} {'SR':>7}\n"
        text += "-" * 55 + "\n"

        # Sort by highest strike rate (optional pro touch)
        batsmen = sorted(
            [b for b in inn["batsman"] if int(b["balls"]) > 0],
            key=lambda x: float(x["strkrate"]),
            reverse=True
        )

        for b in batsmen:
            name = b["name"][:18]  # prevent overflow
            runs = b["runs"]
            balls = b["balls"]
            sr = f"{float(b['strkrate']):.2f}"

            text += f"{name:18} {runs:>4} {balls:>4} {sr:>7}\n"

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
                parse_mode=ParseMode.HTML
            )
            return


        # ================= MATCH LIST =================
        if d in ["live", "recent", "upcoming"]:

            matches = getattr(api, d)()[:10]

            title_map = {
                "live": "🔴 LIVE MATCHES",
                "recent": "🔵 RECENT MATCHES",
                "upcoming": "🟢 UPCOMING MATCHES"
            }

            text = f"<b>{title_map[d]}</b>\n\n"
            buttons = []

            if not matches:
                text += "No matches found."
            else:
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
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            return


        # ================= MATCH DETAIL MENU =================
        if d.startswith("match_"):
            mid = d.split("_")[1]

            await query.message.edit_text(
                "📂 <b>Select Match Details</b>",
                reply_markup=detail_menu(mid),
                parse_mode=ParseMode.HTML
            )
            return


        # ================= SCORECARD =================
        if d.startswith("score_"):
            mid = d.split("_")[1]

            score_data = api.scorecard(mid)
            text = format_scorecard(score_data)

            await query.message.edit_text(
                text,
                reply_markup=detail_menu(mid),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            return


        # ================= SQUADS =================
        if d.startswith("squad_"):
            mid = d.split("_")[1]

            squad_data = api.squads(mid)
            text = format_squads(squad_data)

            await query.message.edit_text(
                text,
                reply_markup=detail_menu(mid),
                parse_mode=ParseMode.HTML
            )
            return

        if d.startswith("sr_"):
            mid = d.split("_")[1]
            data = api.scorecard(mid)

            await query.message.edit_text(
                format_strike_rate(data),
                reply_markup=detail_menu(mid),
                parse_mode=ParseMode.HTML
            )
            return


        # ================= LIVE STATUS =================
        if d.startswith("live_"):
            mid = d.split("_")[1]

            live_data = api.commentary(mid)
            text = format_live(live_data)

            await query.message.edit_text(
                text,
                reply_markup=detail_menu(mid),
                parse_mode=ParseMode.HTML
            )
            return

        if d.startswith("bat_"):
            mid = d.split("_")[1]
            data = api.scorecard(mid)

            await query.message.edit_text(
                format_batting(data),
                reply_markup=detail_menu(mid),
                parse_mode=ParseMode.HTML
             )
            return


        if d.startswith("bowl_"):
            mid = d.split("_")[1]
            data = api.scorecard(mid)

            await query.message.edit_text(
                format_bowling(data),
                reply_markup=detail_menu(mid),
                parse_mode=ParseMode.HTML
            )
            return


    except Exception as e:
        await query.message.edit_text(
            f"⚠ <b>Error Occurred</b>\n\n<code>{e}</code>",
            parse_mode=ParseMode.HTML
        )
# ================= RUN =================
app.run()
