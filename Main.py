import os
import asyncio
import httpx
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = 35362137
API_HASH = "c3c3e167ea09bc85369ca2fa3c1be790"
BOT_TOKEN = "8490783791:AAFT8DygQAO5cC-Bg6yi_D-0c7wOlIKDFdA"
RAPID_API_KEY = "1bf70049e7msh71db390a6f430e7p125822jsnb7c6630377f7"

BASE = "https://cricbuzz-cricket2.p.rapidapi.com"

HEADERS = {
    "x-rapidapi-key": RAPID_API_KEY,
    "x-rapidapi-host": "cricbuzz-cricket2.p.rapidapi.com"
}

app = Client("CricketBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

active_alerts = {}

# ---------------- FETCH ---------------- #

async def fetch(endpoint):
    print("\n[FETCH]", endpoint)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{BASE}{endpoint}", headers=HEADERS)
            print("[STATUS]", r.status_code)
            r.raise_for_status()
            data = r.json()
            print("[JSON KEYS]", list(data.keys()) if isinstance(data, dict) else "Not Dict")
            return data
    except Exception as e:
        print("[FETCH ERROR]", e)
        return {}

# ---------------- SAFE EDIT ---------------- #

async def safe_edit(message, text, markup=None):
    if not text or text.strip() == "":
        text = "⚠️ No data available."

    if len(text) > 4000:
        text = text[:4000]

    try:
        await message.edit_text(text, reply_markup=markup)
    except Exception as e:
        print("[EDIT FAILED]", e)
        try:
            await message.reply_text(text, reply_markup=markup)
        except Exception as e2:
            print("[REPLY FAILED]", e2)

# ---------------- FORMAT SCORE ---------------- #

def format_scorecard(data):
    print("[FORMAT] Called")

    if not data or "scoreCard" not in data:
        print("[FORMAT] No scoreCard key")
        return "⚠️ Scorecard not available."

    if not data["scoreCard"]:
        print("[FORMAT] scoreCard empty")
        return "⚠️ Match not started or data unavailable."

    text = ""

    for inning in data["scoreCard"]:
        team = inning.get("batTeamDetails", {}).get("batTeamName", "Unknown")
        score = inning.get("scoreDetails", {})

        text += f"🏏 {team} – {score.get('runs',0)}/{score.get('wickets',0)} ({score.get('overs',0)} Overs)\n\n"

    return text

# ---------------- START ---------------- #

@app.on_message(filters.command("start"))
async def start(_, message):
    print("[START COMMAND]")

    buttons = [
        [InlineKeyboardButton("🔴 Live", callback_data="live")],
        [InlineKeyboardButton("📅 Upcoming", callback_data="upcoming")],
        [InlineKeyboardButton("📊 Recent", callback_data="recent")]
    ]

    await message.reply_text("🏏 Cricket Center", reply_markup=InlineKeyboardMarkup(buttons))

# ---------------- DEBUG ALL CALLBACKS ---------------- #

@app.on_callback_query()
async def debug_callback(client, callback):
    print("🔥 CALLBACK RECEIVED:", callback.data)
    await callback.answer()

# ---------------- MATCH LIST ---------------- #

@app.on_callback_query(filters.regex("^(live|upcoming|recent)$"))
async def match_list(_, callback):
    print("[MATCH LIST]", callback.data)
    await callback.answer()

    endpoint_map = {
        "live": "/matches/v1/live",
        "upcoming": "/matches/v1/upcoming",
        "recent": "/matches/v1/recent"
    }

    data = await fetch(endpoint_map[callback.data])
    buttons = []

    for t in data.get("typeMatches", []):
        for s in t.get("seriesMatches", []):
            for m in s.get("seriesAdWrapper", {}).get("matches", []):
                info = m.get("matchInfo", {})
                match_id = info.get("matchId")
                name = f"{info.get('team1',{}).get('teamName')} vs {info.get('team2',{}).get('teamName')}"
                if match_id:
                    buttons.append([InlineKeyboardButton(name, callback_data=f"match_{match_id}")])

    if not buttons:
        buttons = [[InlineKeyboardButton("⬅ Back", callback_data="back")]]

    await safe_edit(callback.message, "🏏 Select Match", InlineKeyboardMarkup(buttons))

# ---------------- MATCH MENU ---------------- #

@app.on_callback_query(filters.regex("^match_"))
async def match_menu(_, callback):
    await callback.answer()
    match_id = callback.data.split("_")[1]
    print("[MATCH MENU] ID:", match_id)

    buttons = [
        [InlineKeyboardButton("📈 Scorecard", callback_data=f"score_{match_id}")],
        [InlineKeyboardButton("⬅ Back", callback_data="recent")]
    ]

    await safe_edit(callback.message, "📌 Match Options", InlineKeyboardMarkup(buttons))

# ---------------- SCORE ---------------- #

@app.on_callback_query(filters.regex("^score_"))
async def score_handler(_, callback):
    await callback.answer()
    match_id = callback.data.split("_")[1]
    print("[SCORE CLICKED]", match_id)

    data = await fetch(f"/mcenter/v1/{match_id}/scard")

    print("[RAW SCORE DATA]", data)

    text = format_scorecard(data)

    buttons = [
        [InlineKeyboardButton("🔄 Refresh", callback_data=f"score_{match_id}")],
        [InlineKeyboardButton("⬅ Back", callback_data=f"match_{match_id}")]
    ]

    await safe_edit(callback.message, text, InlineKeyboardMarkup(buttons))

# ---------------- RUN ---------------- #

print("🚀 BOT STARTING...")
app.run()
