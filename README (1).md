# 🍽 Kalori Botu — Qurulum Təlimatı

## Bot nə edir?
- İstifadəçi yemək adı yazır → Claude AI kcal + makro hesablayır
- Admin `/admin` əmri ilə statistika görür (neçə nəfər, kim, neçə sorğu)

---

## 1. Lazımi şeylər
| Şey | Haradan? |
|-----|---------|
| Telegram Bot Token | [@BotFather](https://t.me/BotFather) → `/newbot` |
| Anthropic API Key | [console.anthropic.com](https://console.anthropic.com) |
| Öz Telegram ID-n | [@userinfobot](https://t.me/userinfobot) yazıb öyrən |
| GitHub account | [github.com](https://github.com) |
| Railway account | [railway.app](https://railway.app) (GitHub ilə qeydiyyat) |

---

## 2. GitHub-a yüklə

```bash
git init
git add .
git commit -m "ilk commit"
git branch -M main
git remote add origin https://github.com/SENİN_ADİN/kcal-bot.git
git push -u origin main
```

> ⚠️ `.env` faylı `.gitignore`-dadır — GitHub-a getməyəcək, əla.

---

## 3. Railway-də deploy et

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Repo-nu seç
3. Sol paneldən **Variables** → **Add Variable** düyməsi ilə 3 dəyişəni əlavə et:

```
BOT_TOKEN          =  xxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY  =  sk-ant-xxxxxxxxxxxxxxxx
ADMIN_TELEGRAM_ID  =  123456789
```

4. **Deploy** — qurtardı! 🚀

---

## 4. Bot əmrləri

| Əmr | Kim? | Nə edir? |
|-----|------|----------|
| `/start` | Hamı | Salamlama mesajı |
| `/help` | Hamı | İstifadə qaydası |
| `/admin` | Yalnız sən | Statistika paneli |

Admin panelindən görə bilərsən:
- 👥 Ümumi istifadəçi sayı
- 📋 Tam siyahı (ad, username, qeydiyyat tarixi, sorğu sayı)
- 🔢 Ən aktif 5 nəfər

---

## 5. Yerli test (isteğe bağlı)

```bash
pip install -r requirements.txt

# .env faylı yarat (şablon: .env.example)
cp .env.example .env
# .env-i redaktə et, tokenləri yaz

python bot.py
```
