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
        data = self._get("/matches/v1/live")
        return [m for m in self._extract(data)
                if m["state"] not in ["Complete", "Preview"]]

    def recent(self):
        data = self._get("/matches/v1/recent")
        return [m for m in self._extract(data)
                if m["state"] == "Complete"]

    def upcoming(self):
        data = self._get("/matches/v1/upcoming")
        return [m for m in self._extract(data)
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
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅ Back", callback_data="back")]
    ])

def match_detail_buttons(match_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Scorecard", callback_data=f"score_{match_id}")],
        [InlineKeyboardButton("👥 Squads", callback_data=f"squad_{match_id}")],
        [InlineKeyboardButton("📝 Commentary", callback_data=f"comm_{match_id}")],
        [InlineKeyboardButton("⬅ Back", callback_data="back")]
    ])

# ================= START =================

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "🏏 **ABHI CRICKET BOT**\n\nSelect Option:",
        reply_markup=main_menu()
    )

# ================= CALLBACK =================

@app.on_callback_query()
async def callback_handler(client, query):
    data = query.data

    # ===== BACK =====
    if data == "back":
        await query.message.edit_text(
            "🏏 **ABHI CRICKET BOT**\n\nSelect Option:",
            reply_markup=main_menu()
        )
        return

    # ===== LIVE =====
    if data == "live":
        matches = api.live()[:10]
        buttons = []
        text = "🔴 LIVE MATCHES\n\n"

        for m in matches:
            text += f"{m['team1']} vs {m['team2']}\n{m['status']}\n\n"
            buttons.append(
                [InlineKeyboardButton(
                    f"{m['team1']} vs {m['team2']}",
                    callback_data=f"match_{m['id']}"
                )]
            )

        buttons.append([InlineKeyboardButton("⬅ Back", callback_data="back")])

        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # ===== RECENT =====
    if data == "recent":
        matches = api.recent()[:10]
        buttons = []
        text = "🔵 RECENT MATCHES\n\n"

        for m in matches:
            text += f"{m['team1']} vs {m['team2']}\n{m['status']}\n\n"
            buttons.append(
                [InlineKeyboardButton(
                    f"{m['team1']} vs {m['team2']}",
                    callback_data=f"match_{m['id']}"
                )]
            )

        buttons.append([InlineKeyboardButton("⬅ Back", callback_data="back")])

        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # ===== UPCOMING =====
    if data == "upcoming":
        matches = api.upcoming()[:10]
        buttons = []
        text = "🟢 UPCOMING MATCHES\n\n"

        for m in matches:
            text += f"{m['team1']} vs {m['team2']}\n{m['status']}\n\n"
            buttons.append(
                [InlineKeyboardButton(
                    f"{m['team1']} vs {m['team2']}",
                    callback_data=f"match_{m['id']}"
                )]
            )

        buttons.append([InlineKeyboardButton("⬅ Back", callback_data="back")])

        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # ===== MATCH SELECT =====
    if data.startswith("match_"):
        match_id = data.split("_")[1]
        await query.message.edit_text(
            "Select Match Details:",
            reply_markup=match_detail_buttons(match_id)
        )
        return

    # ===== SCORECARD =====
    if data.startswith("score_"):
        match_id = data.split("_")[1]
        sc = api.scorecard(match_id)
        text = "📊 SCORECARD\n\n"

        if "scorecard" in sc:
            for inn in sc["scorecard"]:
                text += f"{inn['batteamname']} - {inn['score']}/{inn['wickets']}\n"
        else:
            text += "No scorecard available."

        await query.message.edit_text(
            text,
            reply_markup=match_detail_buttons(match_id)
        )
        return

    # ===== SQUADS =====
    if data.startswith("squad_"):
        match_id = data.split("_")[1]
        sq = api.squads(match_id)
        text = "👥 SQUADS\n\n"

        for team_key in ["team1", "team2"]:
            text += sq[team_key]["team"]["teamname"] + "\n"

        await query.message.edit_text(
            text,
            reply_markup=match_detail_buttons(match_id)
        )
        return

    # ===== COMMENTARY =====
    if data.startswith("comm_"):
        match_id = data.split("_")[1]
        cm = api.commentary(match_id)
        text = "📝 COMMENTARY\n\n"

        if "miniscore" in cm:
            text += cm["miniscore"].get("lastwkt", "Live Update")
        else:
            text += "No commentary available."

        await query.message.edit_text(
            text,
            reply_markup=match_detail_buttons(match_id)
        )
        return

# ================= RUN =================
app.run()
