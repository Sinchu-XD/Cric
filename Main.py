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

# ---------------- API FETCH ---------------- #

async def fetch(endpoint, params=None):
    print("\n[FETCH] Endpoint:", endpoint)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{BASE}{endpoint}", headers=HEADERS, params=params)
            print("[FETCH] Status Code:", r.status_code)
            print("[FETCH] Response Length:", len(r.text))
            r.raise_for_status()
            data = r.json()
            print("[FETCH] JSON Keys:", list(data.keys()))
            return data
    except Exception as e:
        print("[FETCH ERROR]:", e)
        return {}

# ---------------- SAFE EDIT ---------------- #

async def safe_edit(message, text, markup=None):
    print("[SAFE_EDIT] Text Length:", len(text) if text else 0)

    if not text or text.strip() == "":
        print("[SAFE_EDIT] Empty text detected")
        text = "⚠️ No data available."

    if len(text) > 4000:
        print("[SAFE_EDIT] Trimming long message")
        text = text[:4000]

    try:
        await message.edit_text(text, reply_markup=markup)
        print("[SAFE_EDIT] Message Edited")
    except Exception as e:
        print("[SAFE_EDIT ERROR - Edit Failed]:", e)
        try:
            await message.reply_text(text, reply_markup=markup)
            print("[SAFE_EDIT] Sent as new message")
        except Exception as e2:
            print("[SAFE_EDIT ERROR - Reply Failed]:", e2)

# ---------------- SCORE FORMATTER ---------------- #

def format_scorecard(data):
    print("[FORMAT] Formatting scorecard")

    if not data:
        print("[FORMAT] Data empty")
        return "⚠️ API returned empty data."

    if "scoreCard" not in data:
        print("[FORMAT] scoreCard key missing")
        return "⚠️ scoreCard key missing in response."

    if not data["scoreCard"]:
        print("[FORMAT] scoreCard empty list")
        return "⚠️ Scorecard not available yet."

    text = ""

    for inning in data["scoreCard"]:
        team = inning.get("batTeamDetails", {}).get("batTeamName", "Unknown")
        score = inning.get("scoreDetails", {})

        print("[FORMAT] Team:", team)

        text += f"🏏 {team} – {score.get('runs',0)}/{score.get('wickets',0)} ({score.get('overs',0)} Overs)\n\n"

    return text

# ---------------- START ---------------- #

@app.on_message(filters.command("start"))
async def start(_, message):
    print("[START] Command received")

    buttons = [
        [InlineKeyboardButton("🔴 Live", callback_data="live")],
        [InlineKeyboardButton("📅 Upcoming", callback_data="upcoming")],
        [InlineKeyboardButton("📊 Recent", callback_data="recent")]
    ]

    await message.reply_text("🏏 Cricket Center", reply_markup=InlineKeyboardMarkup(buttons))

# ---------------- MATCH LIST ---------------- #

@app.on_callback_query(filters.regex("^(live|upcoming|recent)$"))
async def match_list(_, callback):
    print("[MATCH_LIST] Clicked:", callback.data)

    endpoint_map = {
        "live": "/matches/v1/live",
        "upcoming": "/matches/v1/upcoming",
        "recent": "/matches/v1/recent"
    }

    data = await fetch(endpoint_map[callback.data])
    buttons = []

    print("[MATCH_LIST] Processing matches")

    for t in data.get("typeMatches", []):
        for s in t.get("seriesMatches", []):
            for m in s.get("seriesAdWrapper", {}).get("matches", []):
                info = m.get("matchInfo", {})
                match_id = info.get("matchId")
                print("[MATCH_LIST] Found Match ID:", match_id)

                name = f"{info.get('team1',{}).get('teamName')} vs {info.get('team2',{}).get('teamName')}"

                if match_id:
                    buttons.append([InlineKeyboardButton(name, callback_data=f"match_{match_id}")])

    if not buttons:
        print("[MATCH_LIST] No matches found")

    await safe_edit(callback.message, "🏏 Select Match", InlineKeyboardMarkup(buttons))

# ---------------- SCORE ---------------- #

@app.on_callback_query(filters.regex("^score_"))
async def score_handler(_, callback):
    match_id = callback.data.split("_")[1]
    print("[SCORE] Match ID:", match_id)

    data = await fetch(f"/mcenter/v1/{match_id}/scard")

    print("[SCORE] Raw Data:", data)

    text = format_scorecard(data)

    await safe_edit(callback.message, text)

# ---------------- ALERT ON ---------------- #

@app.on_callback_query(filters.regex("^alerton_"))
async def alert_on(client, callback):
    match_id = callback.data.split("_")[1]
    chat_id = callback.message.chat.id

    print("[ALERT ON] Chat:", chat_id, "Match:", match_id)

    active_alerts[chat_id] = {"match_id": match_id, "last_over": None}

    await callback.answer("Alert Activated 🚨", show_alert=True)
    asyncio.create_task(over_monitor(client, chat_id))

# ---------------- OVER MONITOR ---------------- #

async def over_monitor(client, chat_id):
    print("[OVER_MONITOR] Started for chat:", chat_id)

    while chat_id in active_alerts:
        match_id = active_alerts[chat_id]["match_id"]

        print("[OVER_MONITOR] Checking match:", match_id)

        overs = await fetch(f"/mcenter/v1/{match_id}/overs")

        print("[OVER_MONITOR] Overs Data:", overs)

        await asyncio.sleep(35)

app.run()
