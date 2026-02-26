import os
import asyncio
import httpx
from dotenv import load_dotenv
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
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BASE}{endpoint}", headers=HEADERS, params=params)
        r.raise_for_status()
        return r.json()


# ---------------- SAFE SEND ---------------- #

async def safe_edit(message, text, markup=None):
    if len(text) < 4000:
        await message.edit_text(text, reply_markup=markup)
    else:
        await message.edit_text(text[:4000], reply_markup=markup)


# ---------------- SCORECARD FORMATTER ---------------- #

def format_scorecard(data):
    text = ""

    for inning in data.get("scoreCard", []):
        team = inning.get("batTeamDetails", {}).get("batTeamName", "Unknown")
        score = inning.get("scoreDetails", {})

        text += f"🏏 {team} – {score.get('runs',0)}/{score.get('wickets',0)} ({score.get('overs',0)} Overs)\n\n"

        # BATSMEN
        text += "BATSMEN\n"
        text += "---------------------------------\n"

        batsmen = inning.get("batTeamDetails", {}).get("batsmenData", {})

        for b in batsmen.values():
            name = b.get("batName","")
            runs = b.get("runs",0)
            balls = b.get("balls",0)
            fours = b.get("fours",0)
            sixes = b.get("sixes",0)
            sr = b.get("strikeRate",0)
            out = b.get("outDesc","not out")

            text += (
                f"{name}\n"
                f"{runs} ({balls})  4s:{fours}  6s:{sixes}  SR:{sr}\n"
                f"{out}\n\n"
            )

        # EXTRAS
        extras = inning.get("extrasData", {})
        text += f"Extras: {extras.get('total',0)}\n\n"

        # BOWLING
        text += "BOWLING\n"
        text += "---------------------------------\n"

        bowlers = inning.get("bowlTeamDetails", {}).get("bowlersData", {})

        for bw in bowlers.values():
            text += (
                f"{bw.get('bowlName','')}  "
                f"{bw.get('overs',0)}-"
                f"{bw.get('maidens',0)}-"
                f"{bw.get('runs',0)}-"
                f"{bw.get('wickets',0)}\n"
            )

        # FALL OF WICKETS
        text += "\nFall of Wickets:\n"
        for w in inning.get("wicketsData", {}).values():
            text += (
                f"{w.get('wktRuns')}-"
                f"{w.get('wktNbr')} "
                f"({w.get('batName')}, "
                f"{w.get('wktOver')} ov)\n"
            )

        text += "\n\n"

    return text


# ---------------- START ---------------- #

@app.on_message(filters.command("start"))
async def start(_, message):
    buttons = [
        [InlineKeyboardButton("🔴 Live", callback_data="live")],
        [InlineKeyboardButton("📅 Upcoming", callback_data="upcoming")],
        [InlineKeyboardButton("📊 Recent", callback_data="recent")]
    ]
    await message.reply_text("🏏 Cricket Center", reply_markup=InlineKeyboardMarkup(buttons))


# ---------------- MATCH LIST ---------------- #

@app.on_callback_query(filters.regex("^(live|upcoming|recent)$"))
async def match_list(_, callback):
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

    buttons.append([InlineKeyboardButton("⬅ Back", callback_data="back")])
    await safe_edit(callback.message, "🏏 Select Match", InlineKeyboardMarkup(buttons))


# ---------------- MATCH MENU ---------------- #

@app.on_callback_query(filters.regex("^match_"))
async def match_menu(_, callback):
    match_id = callback.data.split("_")[1]

    buttons = [
        [InlineKeyboardButton("📈 Scorecard", callback_data=f"score_{match_id}")],
        [InlineKeyboardButton("🚨 Alert ON", callback_data=f"alerton_{match_id}")],
        [InlineKeyboardButton("🛑 Alert OFF", callback_data=f"alertoff_{match_id}")],
        [InlineKeyboardButton("⬅ Back", callback_data="live")]
    ]

    await safe_edit(callback.message, "📌 Match Options", InlineKeyboardMarkup(buttons))


# ---------------- SCORE HANDLER ---------------- #

@app.on_callback_query(filters.regex("^score_"))
async def score_handler(_, callback):
    match_id = callback.data.split("_")[1]
    data = await fetch(f"/mcenter/v1/{match_id}/scard")

    text = format_scorecard(data)

    buttons = [
        [InlineKeyboardButton("🔄 Refresh", callback_data=f"score_{match_id}")],
        [InlineKeyboardButton("⬅ Back", callback_data=f"match_{match_id}")]
    ]

    await safe_edit(callback.message, text, InlineKeyboardMarkup(buttons))


# ---------------- ALERT ON ---------------- #

@app.on_callback_query(filters.regex("^alerton_"))
async def alert_on(client, callback):
    match_id = callback.data.split("_")[1]
    chat_id = callback.message.chat.id

    active_alerts[chat_id] = {"match_id": match_id, "last_over": None}

    await callback.answer("Alert Activated 🚨", show_alert=True)
    asyncio.create_task(over_monitor(client, chat_id))


# ---------------- ALERT OFF ---------------- #

@app.on_callback_query(filters.regex("^alertoff_"))
async def alert_off(_, callback):
    chat_id = callback.message.chat.id
    active_alerts.pop(chat_id, None)
    await callback.answer("Alert Stopped 🛑", show_alert=True)


# ---------------- OVER MONITOR ---------------- #

async def over_monitor(client, chat_id):
    while chat_id in active_alerts:
        match_id = active_alerts[chat_id]["match_id"]

        try:
            overs = await fetch(f"/mcenter/v1/{match_id}/overs")
            scard = await fetch(f"/mcenter/v1/{match_id}/scard")

            over_list = overs.get("overSummaryList", [])

            if over_list:
                current_over = over_list[0].get("overNum")
                last_over = active_alerts[chat_id]["last_over"]

                if last_over != current_over:
                    active_alerts[chat_id]["last_over"] = current_over

                    score_text = format_scorecard(scard)
                    await client.send_message(chat_id, f"🏏 Over {current_over} Completed\n\n" + score_text[:3500])

        except Exception as e:
            print("Alert Error:", e)

        await asyncio.sleep(35)


# ---------------- BACK ---------------- #

@app.on_callback_query(filters.regex("^back$"))
async def back(_, callback):
    await start(_, callback.message)


# ---------------- RUN ---------------- #

app.run()
