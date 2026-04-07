import os
import json
import datetime
from google import genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ── Config ──────────────────────────────────────────────────────────────────
BOT_TOKEN  = os.environ["BOT_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]
ADMIN_ID   = int(os.environ["ADMIN_TELEGRAM_ID"])
STATS_FILE = "stats.json"

client_gemini = genai.Client(api_key=GEMINI_KEY)

# ── Stats helpers ────────────────────────────────────────────────────────────
def load_stats() -> dict:
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {"users": {}}

def save_stats(data: dict):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def register_user(user):
    data = load_stats()
    uid  = str(user.id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "name":       user.full_name,
            "username":   user.username or "",
            "start_date": datetime.datetime.now().isoformat(),
            "queries":    0
        }
        save_stats(data)

def increment_query(user_id: int):
    data = load_stats()
    uid  = str(user_id)
    if uid in data["users"]:
        data["users"][uid]["queries"] += 1
        save_stats(data)

# ── Gemini qida analizi ──────────────────────────────────────────────────────
def analyse_food(text: str) -> str:
    prompt = f"""
Sən qida analizi mütəxəssisisən. İstifadəçi aşağıdakı məlumatı göndərib:
"{text}"

Əgər bu bir yemək, içki, və ya qida maddəsidirsə:
1. Kcal miqdarını hesabla (standart porsiya üçün)
2. Əsas makro-elementləri ver (protein, yağ, karbohidrat – qramlıqla)
3. Qısa şərh yaz (sağlam/az-sağlam/kalori baxımından)

Cavabı ANCAQ Azərbaycan dilində ver. Format belə olsun:
🍽 **[Yemək adı]**
🔥 Kalori: X kcal (porsiya: ~X q)
💪 Protein: X q
🧈 Yağ: X q
🌾 Karbohidrat: X q
📝 Qeyd: ...

Əgər göndərilən məlumat qida ilə bağlı deyilsə, nəzakətlə izah et.
"""
    response = client_gemini.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text

# ── /start ───────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)
    await update.message.reply_text(
        "👋 Salam! Mən **Kalori Botu**yam.\n\n"
        "İstənilən yemək, içki və ya məhsulun adını yaz — mən kcal və makro dəyərlərini hesablayacağam.\n\n"
        "Məsələn: `100q toyuq döşü`, `bir boşqab plov`, `Coca-Cola 330ml`",
        parse_mode="Markdown"
    )

# ── /help ────────────────────────────────────────────────────────────────────
async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 **İstifadə qaydası:**\n\n"
        "• Yemək adı yaz → kcal + makro dəyərlər alırsan\n"
        "• Miqdar qeyd edə bilərsən: `200q çörək`, `2 yumurta`\n"
        "• Hər hansı sual varsa yaz!\n\n"
        "⚡ Bot Gemini AI ilə işləyir.",
        parse_mode="Markdown"
    )

# ── /admin ───────────────────────────────────────────────────────────────────
async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bu əmr yalnız admin üçündür.")
        return

    kb = [
        [InlineKeyboardButton("👥 İstifadəçi sayı", callback_data="stat_count")],
        [InlineKeyboardButton("📋 Tam siyahı",       callback_data="stat_list")],
        [InlineKeyboardButton("🔢 Ən aktiv 5 nəfər", callback_data="stat_top")],
    ]
    await update.message.reply_text(
        "🛠 **Admin Paneli** — nə görmək istəyirsən?",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

# ── Callback-lar ─────────────────────────────────────────────────────────────
async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("⛔ İcazə yoxdur.")
        return

    data   = load_stats()
    users  = data["users"]
    action = query.data

    if action == "stat_count":
        await query.edit_message_text(
            f"👥 Ümumi istifadəçi sayı: **{len(users)}**",
            parse_mode="Markdown"
        )

    elif action == "stat_list":
        if not users:
            await query.edit_message_text("Hələ istifadəçi yoxdur.")
            return
        lines = ["📋 **İstifadəçi siyahısı:**\n"]
        for i, (uid, u) in enumerate(users.items(), 1):
            uname = f"@{u['username']}" if u['username'] else "—"
            date  = u['start_date'][:10]
            lines.append(f"{i}. {u['name']} ({uname})\n   ID: {uid} | Başlama: {date} | Sorğu: {u['queries']}")
        text = "\n".join(lines)
        if len(text) > 4000:
            text = text[:4000] + "\n...(davam edir)"
        await query.edit_message_text(text, parse_mode="Markdown")

    elif action == "stat_top":
        if not users:
            await query.edit_message_text("Hələ istifadəçi yoxdur.")
            return
        top = sorted(users.items(), key=lambda x: x[1]["queries"], reverse=True)[:5]
        lines = ["🔢 **Ən aktiv 5 istifadəçi:**\n"]
        for i, (uid, u) in enumerate(top, 1):
            lines.append(f"{i}. {u['name']} — {u['queries']} sorğu")
        await query.edit_message_text("\n".join(lines), parse_mode="Markdown")

# ── Mətn mesajları ────────────────────────────────────────────────────────────
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)
    user_text = update.message.text.strip()

    thinking = await update.message.reply_text("⏳ Hesablayıram...")

    try:
        result = analyse_food(user_text)
        increment_query(update.effective_user.id)
        await thinking.edit_text(result, parse_mode="Markdown")
    except Exception as e:
        await thinking.edit_text(f"❌ Xəta baş verdi: {e}")

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot işə düşdü...")
    app.run_polling()

if __name__ == "__main__":
    main()
