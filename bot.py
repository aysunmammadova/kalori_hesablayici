import os
import json
import datetime
from dotenv import load_dotenv
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ── ENV LOAD ────────────────────────────────────────────────────────────────
load_dotenv()

def get_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"❌ Environment variable tapılmadı: {name}")
    return value

BOT_TOKEN  = get_env("BOT_TOKEN")
CLAUDE_KEY = get_env("ANTHROPIC_API_KEY")
ADMIN_ID   = int(get_env("ADMIN_TELEGRAM_ID"))

# ── Claude client ───────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=CLAUDE_KEY)

# ── Stats file ──────────────────────────────────────────────────────────────
STATS_FILE = "stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {"users": {}}

def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def register_user(user):
    data = load_stats()
    uid = str(user.id)

    if uid not in data["users"]:
        data["users"][uid] = {
            "name": user.full_name,
            "username": user.username or "",
            "start_date": datetime.datetime.now().isoformat(),
            "queries": 0
        }
        save_stats(data)

def increment_query(user_id):
    data = load_stats()
    uid = str(user_id)

    if uid in data["users"]:
        data["users"][uid]["queries"] += 1
        save_stats(data)

# ── Claude analiz ───────────────────────────────────────────────────────────
def analyse_food(text: str) -> str:
    prompt = f"""
Sən qida analizi mütəxəssisisən.

İstifadəçi yazdı:
"{text}"

Əgər bu qidadırsa:
- Kalorini hesabla
- Protein / yağ / karbohidrat ver
- Qısa şərh yaz

Format:
🍽 **Ad**
🔥 Kalori: X kcal
💪 Protein: X q
🧈 Yağ: X q
🌾 Karbohidrat: X q
📝 Qeyd: ...

Əgər qida deyilsə, izah et.
Cavab Azərbaycan dilində olsun.
"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    return msg.content[0].text

# ── Commands ────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)

    await update.message.reply_text(
        "👋 Salam! Aysun Məmmədova tərəfindən yaradılmış kalori botuna xoş gəldin.\n\n"
        "Yemək yaz → mən hesablayım 🍽\n\n"
        "Məsələn:\n"
        "`100q toyuq`\n"
        "`1 boşqab plov`",
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Qaydalar:\n"
        "- Yemək adı yaz\n"
        "- Miqdar əlavə edə bilərsən\n\n"
        "Məs: `200q makaron`",
        parse_mode="Markdown"
    )

# ── Admin ───────────────────────────────────────────────────────────────────
async def admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ İcazə yoxdur")

    kb = [
        [InlineKeyboardButton("👥 Say", callback_data="count")],
        [InlineKeyboardButton("🔝 Top 5", callback_data="top")]
    ]

    await update.message.reply_text(
        "Admin panel:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def callbacks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.from_user.id != ADMIN_ID:
        return await q.edit_message_text("⛔")

    data = load_stats()
    users = data["users"]

    if q.data == "count":
        await q.edit_message_text(f"👥 {len(users)} istifadəçi")

    elif q.data == "top":
        top = sorted(users.items(), key=lambda x: x[1]["queries"], reverse=True)[:5]
        text = "🔝 Top istifadəçilər:\n\n"

        for i, (_, u) in enumerate(top, 1):
            text += f"{i}. {u['name']} — {u['queries']}\n"

        await q.edit_message_text(text)

# ── Message handler ─────────────────────────────────────────────────────────
async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)

    msg = await update.message.reply_text("⏳ Hesablayıram...")

    try:
        result = analyse_food(update.message.text)
        increment_query(update.effective_user.id)

        await msg.edit_text(result, parse_mode="Markdown")

    except Exception as e:
        await msg.edit_text(f"❌ Xəta:\n{e}")

# ── Main ────────────────────────────────────────────────────────────────────
def main():
    print("🚀 Bot başlayır...")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.run_polling()

if __name__ == "__main__":
    main()
