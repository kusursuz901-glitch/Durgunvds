import subprocess
import sys
import os
import threading
import time
import re
from datetime import datetime, timedelta

# ================= OTOMATİK PİP YÜKLEME =================
REQUIRED_PACKAGES = [
    "pyTelegramBotAPI",
    "aiogram",
    "colorama",
    "telethon",
    "python-telegram-bot",
    "requests",
    "aiohttp",
    "aiofiles",
    "Pillow",
    "qrcode",
    "cryptg",
    "pyaes",
    "rsa",
    "tgcrypto",
    "pysocks",
    "dnspython",
    "async-timeout",
    "attrs",
    "certifi",
    "charset-normalizer",
    "idna",
    "multidict",
    "yarl",
    "frozenlist",
    "typing-extensions",
    "packaging",
]

print("📦 Paketler kontrol ediliyor / Checking packages...")
for pkg in REQUIRED_PACKAGES:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", pkg],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print(f"  ✅ {pkg}")
        else:
            print(f"  ⚠️ {pkg} yüklenemedi")
    except Exception as e:
        print(f"  ❌ {pkg}: {e}")

print("✅ Paket kontrolü tamamlandı! Bot başlatılıyor...\n")

import telebot
from telebot import types
import sqlite3

TOKEN = "8644852317:AAEmH8T_vm5DZLKLDtAxs-7lbvn0DQyA41U"
ADMIN_ID = 6678969685
OWNER_TAG = "@inledin"

bot = telebot.TeleBot(TOKEN)

# ================= DATABASE - THREAD SAFE =================
db_lock = threading.Lock()

def db_execute(query, params=(), fetchone=False, fetchall=False, commit=False):
    """Thread-safe database işlemi - her çağrıda yeni bağlantı"""
    with db_lock:
        conn = sqlite3.connect("data.db", timeout=10)
        try:
            cur = conn.cursor()
            cur.execute(query, params)
            result = None
            if fetchone:
                result = cur.fetchone()
            elif fetchall:
                result = cur.fetchall()
            if commit:
                conn.commit()
            return result
        except Exception as e:
            print(f"DB Hata: {e}")
            return None
        finally:
            conn.close()

def db_lastrowid(query, params=()):
    """Insert sonrası lastrowid döndür"""
    with db_lock:
        conn = sqlite3.connect("data.db", timeout=10)
        try:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            return cur.lastrowid
        except Exception as e:
            print(f"DB Hata: {e}")
            return None
        finally:
            conn.close()

# ================= TABLOLAR =================
def init_db():
    with db_lock:
        conn = sqlite3.connect("data.db", timeout=10)
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            premium INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0,
            lang TEXT DEFAULT 'tr',
            premium_expire TEXT DEFAULT NULL,
            reg_date TEXT DEFAULT NULL
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bot_name TEXT,
            running INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending'
        )""")
        for col, coltype, default in [
            ("premium_expire", "TEXT", "NULL"),
            ("reg_date", "TEXT", "NULL"),
            ("lang", "TEXT", "'tr'"),
        ]:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col} {coltype} DEFAULT {default}")
            except:
                pass
        try:
            cur.execute("ALTER TABLE bots ADD COLUMN status TEXT DEFAULT 'pending'")
        except:
            pass
        conn.commit()
        conn.close()

init_db()

# ================= ÇEVIRI SİSTEMİ =================
TEXTS = {
    "tr": {
        "welcome": "〽️ Hoş Geldiniz, {name}!\n\n👤 Durumunuz: {status}\n📁 Dosya Sayınız: {count} / {limit}\n⏰ Premium Bitiş: {expire}\n\n🤖 Bu bot Python (.py) betiklerini çalıştırmak için tasarlanmıştır.\n\n👇 Butonları kullanın.",
        "premium_status": "⭐ Premium Kullanıcı",
        "free_status": "🆓 Ücretsiz Kullanıcı",
        "unlimited": "Sınırsız",
        "no_expire": "—",
        "banned": "🚫 Hesabınız yasaklandı.",
        "module_install": "📦 pip modül adı gir:",
        "module_success": "✅ Modül yüklendi.",
        "module_error": "❌ Hata:\n{e}",
        "upload_only_py": "❌ Sadece .py dosya kabul edilir",
        "upload_limit": "❌ Limit dolu. Premium alın.",
        "upload_success": "✅ Dosya yüklendi. Admin onayı bekleniyor.",
        "no_files": "📂 Dosya yok.",
        "waiting": "⏳ Onay Bekliyor",
        "rejected": "❌ Reddedildi",
        "running": "Çalışıyor ✅",
        "stopped": "Duruyor ⏸️",
        "file_not_found": "❌ Dosya bulunamadı.",
        "bot_started": "✅ Bot başlatıldı.",
        "bot_stopped_msg": "✅ Bot durduruldu.",
        "file_deleted": "✅ Dosya silindi.",
        "no_logs": "📄 Log bulunamadı.",
        "logs_title": "📄 Loglar:\n",
        "support_prompt": "✍️ Lütfen mesajınızı yazın. Bu mesaj doğrudan admine iletilecek.",
        "support_sent": "✅ Mesajınız iletildi.",
        "send_py": ".py dosyanızı gönderin",
        "pending_info": "Bu dosya admin onayı bekliyor.",
        "not_approved": "❌ Bu dosya admin tarafından onaylanmadı.",
        "file_not_found_cb": "Dosya bulunamadı.",
        "approved_notify": "✅ Dosyanız onaylandı ve çalıştırılmaya hazır: `{filename}`",
        "rejected_notify": "❌ Dosyanız reddedildi: `{filename}`",
        "bot_crashed": "⚠️ Botunuz çöktü veya durdu: `{filename}`\nYeniden başlatmak için Dosyalarım menüsünü kullanın.",
        "enc_file": "🔐 Şifreli/obfuscate dosya kabul edilmez!\nLütfen normal .py dosyası yükleyin.\nYardım için: {owner}",
        "pip_installing": "📥 Pip paketleri kuruluyor...\n\n{bar} %{percent}\n📦 {pkg}",
        "pip_done": "✅ Tüm paketler kuruldu! Bot kullanıma hazır.",
        "btn_module": "📦 Modül Yükle",
        "btn_upload": "📂 Dosya Yükle",
        "btn_files": "📂 Dosyalarım",
        "btn_support": "📞 Destek & İletişim",
        "btn_profile": "👤 Profilim",
        "select_lang": "🌐 Lütfen bir dil seçin:\nPlease select a language:",
        "lang_selected": "✅ Türkçe seçildi!",
        "profile_text": (
            "👤 *Kullanıcı Profili*\n\n"
            "🆔 ID: `{uid}`\n"
            "📛 İsim: {name}\n"
            "⭐ Durum: {status}\n"
            "⏰ Premium Bitiş: {expire}\n"
            "📁 Dosya: {count} / {limit}\n"
            "🌐 Dil: {lang}\n"
            "📅 Kayıt: {reg_date}"
        ),
        "stats_text": (
            "📊 *İstatistikler*\n\n"
            "👥 Toplam Kullanıcı: {users}\n"
            "⭐ Premium Kullanıcı: {premiums}\n"
            "📁 Toplam Dosya: {files}\n"
            "🤖 Aktif Bot: {running}\n"
            "⏳ Onay Bekleyen: {pending}"
        ),
        "warning_dangerous": (
            "⚠️ *Tehlikeli Kod Uyarısı*\n\n"
            "👤 Kullanıcı: {name}\n"
            "🆔 ID: {uid}\n"
            "📄 Dosya: {filename}\n\n"
            "🚨 Tespit Edilen:\n{findings}\n\n"
            "ℹ️ Dosya yüklendi, dikkatli olun."
        ),
    },
    "en": {
        "welcome": "〽️ Welcome, {name}!\n\n👤 Status: {status}\n📁 Files: {count} / {limit}\n⏰ Premium Expires: {expire}\n\n🤖 This bot is designed to run Python (.py) scripts.\n\n👇 Use the buttons below.",
        "premium_status": "⭐ Premium User",
        "free_status": "🆓 Free User",
        "unlimited": "Unlimited",
        "no_expire": "—",
        "banned": "🚫 Your account has been banned.",
        "module_install": "📦 Enter pip module name:",
        "module_success": "✅ Module installed.",
        "module_error": "❌ Error:\n{e}",
        "upload_only_py": "❌ Only .py files are accepted",
        "upload_limit": "❌ Limit reached. Get Premium.",
        "upload_success": "✅ File uploaded. Waiting for admin approval.",
        "no_files": "📂 No files found.",
        "waiting": "⏳ Waiting for Approval",
        "rejected": "❌ Rejected",
        "running": "Running ✅",
        "stopped": "Stopped ⏸️",
        "file_not_found": "❌ File not found.",
        "bot_started": "✅ Bot started.",
        "bot_stopped_msg": "✅ Bot stopped.",
        "file_deleted": "✅ File deleted.",
        "no_logs": "📄 No logs found.",
        "logs_title": "📄 Logs:\n",
        "support_prompt": "✍️ Please write your message. It will be forwarded to the admin.",
        "support_sent": "✅ Your message has been sent.",
        "send_py": "Send your .py file",
        "pending_info": "This file is waiting for admin approval.",
        "not_approved": "❌ This file has not been approved by admin.",
        "file_not_found_cb": "File not found.",
        "approved_notify": "✅ Your file has been approved and is ready to run: `{filename}`",
        "rejected_notify": "❌ Your file has been rejected: `{filename}`",
        "bot_crashed": "⚠️ Your bot crashed or stopped: `{filename}`\nUse My Files menu to restart.",
        "enc_file": "🔐 Encrypted/obfuscated files are not accepted!\nPlease upload a normal .py file.\nFor help: {owner}",
        "pip_installing": "📥 Installing pip packages...\n\n{bar} %{percent}\n📦 {pkg}",
        "pip_done": "✅ All packages installed! Bot is ready.",
        "btn_module": "📦 Install Module",
        "btn_upload": "📂 Upload File",
        "btn_files": "📂 My Files",
        "btn_support": "📞 Support & Contact",
        "btn_profile": "👤 My Profile",
        "select_lang": "🌐 Lütfen bir dil seçin:\nPlease select a language:",
        "lang_selected": "✅ English selected!",
        "profile_text": (
            "👤 *User Profile*\n\n"
            "🆔 ID: `{uid}`\n"
            "📛 Name: {name}\n"
            "⭐ Status: {status}\n"
            "⏰ Premium Expires: {expire}\n"
            "📁 Files: {count} / {limit}\n"
            "🌐 Language: {lang}\n"
            "📅 Registered: {reg_date}"
        ),
        "stats_text": (
            "📊 *Statistics*\n\n"
            "👥 Total Users: {users}\n"
            "⭐ Premium Users: {premiums}\n"
            "📁 Total Files: {files}\n"
            "🤖 Active Bots: {running}\n"
            "⏳ Pending Approval: {pending}"
        ),
        "warning_dangerous": (
            "⚠️ *Dangerous Code Warning*\n\n"
            "👤 User: {name}\n"
            "🆔 ID: {uid}\n"
            "📄 File: {filename}\n\n"
            "🚨 Detected:\n{findings}\n\n"
            "ℹ️ File uploaded but be careful."
        ),
    }
}

def t(uid, key, **kwargs):
    lang = get_user_lang(uid)
    text = TEXTS.get(lang, TEXTS["tr"]).get(key, TEXTS["tr"].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text

# ================= DİL FONKSİYONLARI =================
_lang_cache = {}

def get_user_lang(uid):
    if uid in _lang_cache:
        return _lang_cache[uid]
    row = db_execute("SELECT lang FROM users WHERE user_id=?", (uid,), fetchone=True)
    lang = row[0] if row and row[0] else "tr"
    _lang_cache[uid] = lang
    return lang

def set_user_lang(uid, lang):
    _lang_cache[uid] = lang
    db_execute("UPDATE users SET lang=? WHERE user_id=?", (lang, uid), commit=True)

# ================= STATE =================
running_processes = {}
running_lock = threading.Lock()
bot_logs = {}
logs_lock = threading.Lock()
admin_step = {}
support_wait = {}
announce_wait = {}
lang_wait = {}
watchdog_restarting = set()

# ================= LOG =================
def add_log(bot_id, text):
    with logs_lock:
        if bot_id not in bot_logs:
            bot_logs[bot_id] = []
        bot_logs[bot_id].append(text)

# ================= MENÜLER =================
def main_menu(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(t(uid, "btn_module"))
    kb.add(t(uid, "btn_upload"))
    kb.add(t(uid, "btn_files"))
    kb.row(t(uid, "btn_support"), t(uid, "btn_profile"))
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⭐ Premium Ver", "👤 Kullanıcı Yasakla / Aç")
    kb.add("🤖 Aktif Botlar")
    kb.add("⛔ Bot Kapat")
    kb.add("🛑 Tüm Botları Kapat")
    kb.add("📢 Duyuru Gönder")
    kb.add("⬅️ Çıkış")
    return kb

def lang_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang_tr"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    return kb

# ================= PREMIUM KONTROL =================
def check_premium_expire():
    while True:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rows = db_execute(
                "SELECT user_id FROM users WHERE premium=1 AND premium_expire IS NOT NULL AND premium_expire < ?",
                (now,), fetchall=True
            )
            if rows:
                for row in rows:
                    uid = row[0]
                    db_execute("UPDATE users SET premium=0, premium_expire=NULL WHERE user_id=?", (uid,), commit=True)
                    try:
                        lang = get_user_lang(uid)
                        msg = "⭐ Premium süreniz doldu." if lang == "tr" else "⭐ Your premium has expired."
                        bot.send_message(uid, msg)
                    except:
                        pass
        except Exception as e:
            print(f"Premium kontrol hatası: {e}")
        time.sleep(1800)

threading.Thread(target=check_premium_expire, daemon=True).start()

# ================= ŞİFRELİ DOSYA KONTROLÜ =================
OBFUSCATION_PATTERNS = [
    r"exec\s*\(\s*__import__",
    r"eval\s*\(\s*__import__",
    r"marshal\.loads",
    r"zlib\.decompress.*exec",
    r"base64\.b64decode.*exec",
    r"exec\s*\(.*decode\(",
]

def is_encrypted_file(content: str) -> bool:
    hex_count = len(re.findall(r'\\x[0-9a-fA-F]{2}', content))
    if hex_count > 30:
        return True
    for pattern in OBFUSCATION_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    if len(content) > 100:
        printable = sum(1 for c in content if c.isprintable() or c in '\n\r\t')
        if printable / len(content) < 0.80:
            return True
    return False

# ================= ZARARLI KOD TARAMA =================
DANGEROUS_PATTERNS = {
    "os.system": "Sistem komutu çalıştırma",
    "subprocess.call": "Alt süreç çalıştırma",
    "subprocess.Popen": "Alt süreç açma",
    "shutil.rmtree": "Klasör silme",
    "os.remove": "Dosya silme",
    "os.rmdir": "Klasör silme",
    "__import__('os')": "Gizli os import",
    "open('/etc": "Sistem dosyası erişimi",
    "open('/root": "Root dizini erişimi",
    "ctypes": "C kütüphanesi erişimi",
    "paramiko": "SSH bağlantısı",
    "keylogger": "Klavye kaydedici",
    "pynput": "Klavye/fare kontrolü",
}

def scan_dangerous_code(content: str) -> list:
    findings = []
    for pattern, desc in DANGEROUS_PATTERNS.items():
        if pattern.lower() in content.lower():
            findings.append(f"• `{pattern}` — {desc}")
    return findings

# ================= PİP BİLDİRİMİ =================
def notify_pip_install(uid, packages):
    total = len(packages)
    try:
        msg = bot.send_message(uid, "📥 Pip paketleri kontrol ediliyor...")
        msg_id = msg.message_id
        for i, pkg in enumerate(packages):
            percent = int(((i + 1) / total) * 100)
            filled = int(percent / 10)
            bar = "█" * filled + "░" * (10 - filled)
            try:
                bot.edit_message_text(
                    chat_id=uid,
                    message_id=msg_id,
                    text=t(uid, "pip_installing", bar=bar, percent=percent, pkg=pkg)
                )
            except:
                pass
            time.sleep(0.15)
        bot.edit_message_text(chat_id=uid, message_id=msg_id, text=t(uid, "pip_done"))
    except Exception as e:
        print(f"Pip bildirim hatası: {e}")

# ================= START =================
@bot.message_handler(commands=["start"])
def start(message):
    u = message.from_user
    uid = u.id
    existing = db_execute("SELECT user_id FROM users WHERE user_id=?", (uid,), fetchone=True)
    if not existing:
        reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db_execute("INSERT INTO users (user_id, name, reg_date) VALUES (?, ?, ?)", (uid, u.first_name, reg_date), commit=True)
        bot.send_message(uid, TEXTS["tr"]["select_lang"], reply_markup=lang_keyboard())
        lang_wait[uid] = True
        return

    row = db_execute("SELECT premium, banned FROM users WHERE user_id=?", (uid,), fetchone=True)
    if not row:
        return
    if row[1]:
        bot.send_message(uid, t(uid, "banned"))
        return
    _send_welcome(uid, u, row[0])

def _send_welcome(uid, u, premium):
    try:
        photos = bot.get_user_profile_photos(uid, limit=1)
        if photos.total_count:
            bot.send_photo(uid, photos.photos[0][0].file_id)
    except:
        pass
    count_row = db_execute("SELECT COUNT(*) FROM bots WHERE user_id=?", (uid,), fetchone=True)
    count = count_row[0] if count_row else 0
    expire_row = db_execute("SELECT premium_expire FROM users WHERE user_id=?", (uid,), fetchone=True)
    expire = expire_row[0] if expire_row and expire_row[0] else None
    status_text = t(uid, "premium_status") if premium else t(uid, "free_status")
    limit_text = t(uid, "unlimited") if premium else "1"
    expire_text = expire[:10] if expire else t(uid, "no_expire")
    bot.send_message(uid, t(uid, "welcome", name=u.first_name, status=status_text, count=count, limit=limit_text, expire=expire_text), reply_markup=main_menu(uid))

# ================= PROFİL =================
@bot.message_handler(commands=["profil", "profile"])
def profile_cmd(message):
    show_profile(message)

@bot.message_handler(func=lambda m: m.text in [TEXTS["tr"]["btn_profile"], TEXTS["en"]["btn_profile"]])
def show_profile(message):
    uid = message.from_user.id
    row = db_execute("SELECT name, premium, lang, premium_expire, reg_date FROM users WHERE user_id=?", (uid,), fetchone=True)
    if not row:
        return
    name, premium, lang, expire, reg_date = row
    count_row = db_execute("SELECT COUNT(*) FROM bots WHERE user_id=?", (uid,), fetchone=True)
    count = count_row[0] if count_row else 0
    status_text = t(uid, "premium_status") if premium else t(uid, "free_status")
    limit_text = t(uid, "unlimited") if premium else "1"
    expire_text = expire[:10] if expire else t(uid, "no_expire")
    reg_text = reg_date[:10] if reg_date else "—"
    lang_text = "🇹🇷 Türkçe" if lang == "tr" else "🇬🇧 English"
    bot.send_message(uid, t(uid, "profile_text", uid=uid, name=name, status=status_text, expire=expire_text, count=count, limit=limit_text, lang=lang_text, reg_date=reg_text), parse_mode="Markdown")

# ================= STATS =================
@bot.message_handler(commands=["stats"])
def stats(message):
    uid = message.from_user.id
    users = db_execute("SELECT COUNT(*) FROM users", fetchone=True)[0]
    premiums = db_execute("SELECT COUNT(*) FROM users WHERE premium=1", fetchone=True)[0]
    files = db_execute("SELECT COUNT(*) FROM bots", fetchone=True)[0]
    running_count = db_execute("SELECT COUNT(*) FROM bots WHERE running=1", fetchone=True)[0]
    pending = db_execute("SELECT COUNT(*) FROM bots WHERE status='pending'", fetchone=True)[0]
    bot.send_message(uid, t(uid, "stats_text", users=users, premiums=premiums, files=files, running=running_count, pending=pending), parse_mode="Markdown")

# ================= DİL =================
@bot.message_handler(commands=["lang", "language", "dil"])
def change_lang(message):
    bot.send_message(message.chat.id, TEXTS["tr"]["select_lang"], reply_markup=lang_keyboard())

# ================= ADMIN =================
@bot.message_handler(commands=["adminpanel"])
def adminpanel(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "👑 Admin Panel", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "⬅️ Çıkış" and m.from_user.id == ADMIN_ID)
def exit_admin(message):
    bot.send_message(message.chat.id, "Çıkıldı.", reply_markup=main_menu(message.from_user.id))

@bot.message_handler(func=lambda m: m.text == "📢 Duyuru Gönder" and m.from_user.id == ADMIN_ID)
def announce_prompt(message):
    announce_wait[message.from_user.id] = True
    bot.send_message(message.chat.id, "📢 Duyuruyu yazın:")

@bot.message_handler(func=lambda m: m.from_user.id in announce_wait)
def announce_send(message):
    announce_wait.pop(message.from_user.id, None)
    rows = db_execute("SELECT user_id FROM users", fetchall=True)
    sent = 0
    if rows:
        for row in rows:
            try:
                bot.send_message(row[0], f"📢 *Duyuru / Announcement*\n\n{message.text}", parse_mode="Markdown")
                sent += 1
            except:
                pass
    bot.send_message(ADMIN_ID, f"📢 Gönderildi. Toplam: {sent}")

@bot.message_handler(func=lambda m: m.text == "⭐ Premium Ver" and m.from_user.id == ADMIN_ID)
def premium_prompt(message):
    admin_step[message.from_user.id] = "premium"
    bot.send_message(message.chat.id, "🆔 ID ve Gün gir:\nÖrnek: 123456789 30\n(0 = sınırsız)")

@bot.message_handler(func=lambda m: admin_step.get(m.from_user.id) == "premium")
def premium_set(message):
    try:
        parts = message.text.strip().split()
        uid = int(parts[0])
        days = int(parts[1]) if len(parts) > 1 else 0
        existing = db_execute("SELECT user_id FROM users WHERE user_id=?", (uid,), fetchone=True)
        if not existing:
            bot.send_message(message.chat.id, "❌ Kullanıcı bulunamadı.")
        else:
            if days > 0:
                expire_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
                db_execute("UPDATE users SET premium=1, premium_expire=? WHERE user_id=?", (expire_date, uid), commit=True)
                expire_info = f"{days} gün ({expire_date[:10]})"
            else:
                db_execute("UPDATE users SET premium=1, premium_expire=NULL WHERE user_id=?", (uid,), commit=True)
                expire_info = "Sınırsız"
            bot.send_message(message.chat.id, f"✅ {uid} Premium yapıldı. Süre: {expire_info}")
            lang = get_user_lang(uid)
            msg = (f"⭐ Tebrikler! Premium oldunuz.\n⏰ Süre: {expire_info}" if lang == "tr"
                   else f"⭐ Congratulations! You are now Premium.\n⏰ Duration: {expire_info}")
            bot.send_message(uid, msg)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Hata: {e}\nFormat: ID GUN")
    admin_step.pop(message.from_user.id, None)

@bot.message_handler(func=lambda m: m.text == "👤 Kullanıcı Yasakla / Aç" and m.from_user.id == ADMIN_ID)
def ban_prompt(message):
    admin_step[message.from_user.id] = "ban"
    bot.send_message(message.chat.id, "🆔 Kullanıcı ID:")

@bot.message_handler(func=lambda m: admin_step.get(m.from_user.id) == "ban")
def ban_user(message):
    try:
        uid = int(message.text)
        row = db_execute("SELECT banned FROM users WHERE user_id=?", (uid,), fetchone=True)
        if not row:
            bot.send_message(message.chat.id, "❌ Kullanıcı yok.")
        else:
            new_val = 0 if row[0] == 1 else 1
            db_execute("UPDATE users SET banned=? WHERE user_id=?", (new_val, uid), commit=True)
            bot.send_message(message.chat.id, f"✅ {'Açıldı' if new_val == 0 else 'Yasaklandı'}.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Hata: {e}")
    admin_step.pop(message.from_user.id, None)

@bot.message_handler(func=lambda m: m.text == "🤖 Aktif Botlar" and m.from_user.id == ADMIN_ID)
def active_bots(message):
    rows = db_execute("SELECT id, user_id, bot_name FROM bots WHERE running=1", fetchall=True)
    if not rows:
        bot.send_message(message.chat.id, "Aktif bot yok.")
        return
    text = "🔥 Aktif Botlar:\n\n"
    for r in rows:
        text += f"ID: {r[0]} | Kullanıcı: {r[1]} | Dosya: {r[2]}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "⛔ Bot Kapat" and m.from_user.id == ADMIN_ID)
def stop_bot_prompt(message):
    admin_step[message.from_user.id] = "stopbot_full"
    bot.send_message(message.chat.id, "🆔 KullanıcıID DosyaAdı\nÖrnek: 12345678 dosya.py")

@bot.message_handler(func=lambda m: admin_step.get(m.from_user.id) == "stopbot_full")
def stop_bot_full(message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ Format: KullanıcıID DosyaAdı")
            admin_step.pop(message.from_user.id, None)
            return
        uid, filename = int(parts[0]), parts[1]
        row = db_execute("SELECT id FROM bots WHERE user_id=? AND bot_name=?", (uid, filename), fetchone=True)
        if not row:
            bot.send_message(message.chat.id, "❌ Bot bulunamadı.")
        else:
            bid = row[0]
            with running_lock:
                proc = running_processes.pop(bid, None)
            if proc:
                proc.terminate()
            db_execute("UPDATE bots SET running=0 WHERE id=?", (bid,), commit=True)
            watchdog_restarting.discard(bid)
            add_log(bid, "Bot admin tarafından durduruldu ⏸️")
            bot.send_message(message.chat.id, f"✅ {filename} durduruldu.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Hata: {e}")
    admin_step.pop(message.from_user.id, None)

@bot.message_handler(func=lambda m: m.text == "🛑 Tüm Botları Kapat" and m.from_user.id == ADMIN_ID)
def stop_all(message):
    with running_lock:
        for p in running_processes.values():
            try:
                p.terminate()
            except:
                pass
        running_processes.clear()
    watchdog_restarting.clear()
    db_execute("UPDATE bots SET running=0", commit=True)
    bot.send_message(message.chat.id, "✅ Tüm botlar durduruldu.")

# ================= MODÜL YÜKLE =================
@bot.message_handler(func=lambda m: m.text in [TEXTS["tr"]["btn_module"], TEXTS["en"]["btn_module"]])
def mod_prompt(message):
    uid = message.from_user.id
    msg = bot.send_message(message.chat.id, t(uid, "module_install"))
    bot.register_next_step_handler(msg, mod_install)

def mod_install(message):
    uid = message.from_user.id
    pkg = message.text.strip()

    def do_install():
        try:
            bar_msg = bot.send_message(uid, f"📥 {pkg} kuruluyor...\n\n░░░░░░░░░░ %0\n📦 {pkg}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg], timeout=120)
            try:
                bot.edit_message_text(chat_id=uid, message_id=bar_msg.message_id, text=f"✅ {pkg} kuruldu!\n\n██████████ %100\n📦 {pkg}")
            except:
                pass
            bot.send_message(message.chat.id, t(uid, "module_success"))
        except Exception as e:
            bot.send_message(message.chat.id, t(uid, "module_error", e=e))

    threading.Thread(target=do_install, daemon=True).start()

# ================= DOSYA YÜKLE =================
@bot.message_handler(func=lambda m: m.text in [TEXTS["tr"]["btn_upload"], TEXTS["en"]["btn_upload"]])
def upload_prompt(message):
    bot.send_message(message.chat.id, t(message.from_user.id, "send_py"))

@bot.message_handler(content_types=["document"])
def upload(message):
    uid = message.from_user.id
    fname = message.document.file_name
    if not fname.endswith(".py"):
        return bot.reply_to(message, t(uid, "upload_only_py"))

    row = db_execute("SELECT premium FROM users WHERE user_id=?", (uid,), fetchone=True)
    if not row:
        return
    premium = row[0]
    count_row = db_execute("SELECT COUNT(*) FROM bots WHERE user_id=?", (uid,), fetchone=True)
    c = count_row[0] if count_row else 0
    if not premium and c >= 1:
        return bot.reply_to(message, t(uid, "upload_limit"))

    file_info = bot.get_file(message.document.file_id)
    data = bot.download_file(file_info.file_path)

    # Şifreli dosya kontrolü
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        return bot.reply_to(message, t(uid, "enc_file", owner=OWNER_TAG))

    if is_encrypted_file(content):
        return bot.reply_to(message, t(uid, "enc_file", owner=OWNER_TAG))

    # Dosya adı çakışma
    filename = fname
    base, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(filename):
        filename = f"{base}_{counter}{ext}"
        counter += 1

    with open(filename, "wb") as f:
        f.write(data)

    # Zararlı kod tarama
    findings = scan_dangerous_code(content)

    bot_id = db_lastrowid("INSERT INTO bots (user_id, bot_name, status) VALUES (?, ?, ?)", (uid, filename, 'pending'))
    bot.reply_to(message, t(uid, "upload_success"))

    if findings:
        bot.send_message(ADMIN_ID, t(ADMIN_ID, "warning_dangerous", name=message.from_user.first_name, uid=uid, filename=filename, findings="\n".join(findings)), parse_mode="Markdown")

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Onayla", callback_data=f"approve_{bot_id}"),
        types.InlineKeyboardButton("❌ Reddet", callback_data=f"reject_{bot_id}")
    )
    with open(filename, "rb") as f:
        bot.send_document(ADMIN_ID, f, caption=f"📂 Yeni Dosya\n👤 {message.from_user.first_name}\n🆔 {uid}\n📄 {filename}", reply_markup=kb)

# ================= DOSYALARIM =================
@bot.message_handler(func=lambda m: m.text in [TEXTS["tr"]["btn_files"], TEXTS["en"]["btn_files"]])
def files(message):
    uid = message.from_user.id
    rows = db_execute("SELECT id, bot_name, running, status FROM bots WHERE user_id=?", (uid,), fetchall=True)
    if not rows:
        return bot.send_message(uid, t(uid, "no_files"))
    for row in rows:
        bot_id, bot_name, running, status = row
        if status == 'pending':
            durum = t(uid, "waiting")
        elif status == 'rejected':
            durum = t(uid, "rejected")
        else:
            durum = t(uid, "running") if running else t(uid, "stopped")
        kb = types.InlineKeyboardMarkup()
        if status == 'approved':
            kb.row(
                types.InlineKeyboardButton("▶️ Başlat / Start", callback_data=f"start_{bot_id}"),
                types.InlineKeyboardButton("⛔ Durdur / Stop", callback_data=f"stop_{bot_id}")
            )
            kb.row(
                types.InlineKeyboardButton("❌ Sil / Delete", callback_data=f"delete_{bot_id}"),
                types.InlineKeyboardButton("📄 Log", callback_data=f"log_{bot_id}")
            )
        else:
            kb.row(
                types.InlineKeyboardButton("ℹ️ Onay Bekliyor", callback_data=f"info_{bot_id}"),
                types.InlineKeyboardButton("❌ Sil / Delete", callback_data=f"delete_{bot_id}")
            )
        bot.send_message(uid, f"📄 {bot_name}\n🆔 ID: {bot_id}\nDurum / Status: {durum}", reply_markup=kb)

# ================= BOT ÇALIŞTIRMA =================
def run_bot_with_log(bot_id, filename, owner_uid):
    def target():
        watchdog_restarting.discard(bot_id)
        try:
            proc = subprocess.Popen([sys.executable, filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            with running_lock:
                running_processes[bot_id] = proc
            db_execute("UPDATE bots SET running=1, status='approved' WHERE id=?", (bot_id,), commit=True)
            add_log(bot_id, "Bot başlatıldı ✅")

            def read_stream(stream):
                for line in stream:
                    stripped = line.strip()
                    if stripped:
                        add_log(bot_id, stripped)

            t1 = threading.Thread(target=read_stream, args=(proc.stdout,), daemon=True)
            t2 = threading.Thread(target=read_stream, args=(proc.stderr,), daemon=True)
            t1.start(); t2.start()
            proc.wait()
            t1.join(timeout=2); t2.join(timeout=2)

            # Beklenmedik duruş kontrolü
            row = db_execute("SELECT running FROM bots WHERE id=?", (bot_id,), fetchone=True)
            if row and row[0] == 1 and bot_id not in watchdog_restarting:
                db_execute("UPDATE bots SET running=0 WHERE id=?", (bot_id,), commit=True)
                with running_lock:
                    running_processes.pop(bot_id, None)
                add_log(bot_id, "Bot beklenmedik şekilde durdu ⚠️")
                try:
                    bot.send_message(owner_uid, t(owner_uid, "bot_crashed", filename=filename), parse_mode="Markdown")
                except:
                    pass

        except ModuleNotFoundError as e:
            missing = str(e).split("'")[1] if "'" in str(e) else str(e)
            add_log(bot_id, f"Eksik modül: {missing}")
            db_execute("UPDATE bots SET running=0 WHERE id=?", (bot_id,), commit=True)
            with running_lock:
                running_processes.pop(bot_id, None)
            try:
                bot.send_message(owner_uid, f"❌ Eksik modül: `{missing}`\n📦 Modül Yükle ile kurun.", parse_mode="Markdown")
            except:
                pass
        except Exception as e:
            add_log(bot_id, f"Hata: {e}")
            db_execute("UPDATE bots SET running=0 WHERE id=?", (bot_id,), commit=True)
            with running_lock:
                running_processes.pop(bot_id, None)

    threading.Thread(target=target, daemon=True).start()

def get_bot_info(bot_id):
    row = db_execute("SELECT bot_name, user_id FROM bots WHERE id=?", (bot_id,), fetchone=True)
    return (row[0], row[1]) if row else (None, None)

# ================= 5 DAKİKADA BİR WATCHDOG =================
def watchdog():
    time.sleep(60)
    while True:
        try:
            rows = db_execute("SELECT id, bot_name, user_id FROM bots WHERE running=1 AND status='approved'", fetchall=True)
            if rows:
                for row in rows:
                    bot_id, filename, owner_uid = row
                    if bot_id in watchdog_restarting:
                        continue
                    with running_lock:
                        proc = running_processes.get(bot_id)
                    if proc is None or proc.poll() is not None:
                        if os.path.exists(filename):
                            watchdog_restarting.add(bot_id)
                            add_log(bot_id, "⏱️ Watchdog: Yeniden başlatılıyor...")
                            run_bot_with_log(bot_id, filename, owner_uid)
                        else:
                            db_execute("UPDATE bots SET running=0 WHERE id=?", (bot_id,), commit=True)
        except Exception as e:
            print(f"Watchdog hatası: {e}")
        time.sleep(300)

threading.Thread(target=watchdog, daemon=True).start()

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    if call.data.startswith("lang_"):
        lang = call.data.split("_")[1]
        uid = call.from_user.id
        existing = db_execute("SELECT user_id FROM users WHERE user_id=?", (uid,), fetchone=True)
        if not existing:
            reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db_execute("INSERT INTO users (user_id, name, lang, reg_date) VALUES (?, ?, ?, ?)", (uid, call.from_user.first_name, lang, reg_date), commit=True)
        else:
            set_user_lang(uid, lang)
        lang_wait.pop(uid, None)
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=TEXTS[lang]["lang_selected"])
        except:
            pass
        row = db_execute("SELECT premium, banned FROM users WHERE user_id=?", (uid,), fetchone=True)
        if row:
            if row[1]:
                bot.send_message(uid, t(uid, "banned"))
                return
            _send_welcome(uid, call.from_user, row[0])
        # Yeni kullanıcıya pip animasyonu
        threading.Thread(target=notify_pip_install, args=(uid, REQUIRED_PACKAGES), daemon=True).start()
        return

    try:
        action, bot_id_str = call.data.split("_", 1)
        bot_id = int(bot_id_str)
    except:
        return

    uid = call.from_user.id

    if action == "approve":
        if uid != ADMIN_ID:
            return
        row = db_execute("SELECT user_id, bot_name FROM bots WHERE id=? AND status='pending'", (bot_id,), fetchone=True)
        if not row:
            bot.answer_callback_query(call.id, "Zaten tamamlanmış.", show_alert=True)
            return
        target_uid, filename = row
        db_execute("UPDATE bots SET status='approved' WHERE id=?", (bot_id,), commit=True)
        try:
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption="✅ ONAYLANDI\n" + (call.message.caption or ""))
        except:
            pass
        bot.send_message(target_uid, t(target_uid, "approved_notify", filename=filename), parse_mode="Markdown")

    elif action == "reject":
        if uid != ADMIN_ID:
            return
        row = db_execute("SELECT user_id, bot_name FROM bots WHERE id=? AND status='pending'", (bot_id,), fetchone=True)
        if not row:
            bot.answer_callback_query(call.id, "Zaten tamamlanmış.", show_alert=True)
            return
        target_uid, filename = row
        if os.path.exists(filename):
            os.remove(filename)
        db_execute("DELETE FROM bots WHERE id=?", (bot_id,), commit=True)
        try:
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption="❌ REDDEDİLDİ\n" + (call.message.caption or ""))
        except:
            pass
        bot.send_message(target_uid, t(target_uid, "rejected_notify", filename=filename), parse_mode="Markdown")

    elif action == "info":
        bot.answer_callback_query(call.id, t(uid, "pending_info"), show_alert=True)

    else:
        row = db_execute("SELECT status FROM bots WHERE id=?", (bot_id,), fetchone=True)
        if not row:
            bot.answer_callback_query(call.id, t(uid, "file_not_found_cb"), show_alert=True)
            return
        status = row[0]

        if action in ("start", "stop") and status != "approved":
            bot.answer_callback_query(call.id, t(uid, "not_approved"), show_alert=True)
            return

        if action == "start":
            filename, owner_uid = get_bot_info(bot_id)
            if not filename or not os.path.exists(filename):
                bot.send_message(uid, t(uid, "file_not_found"))
                return
            run_bot_with_log(bot_id, filename, owner_uid)
            bot.send_message(uid, t(uid, "bot_started"))

        elif action == "stop":
            with running_lock:
                proc = running_processes.pop(bot_id, None)
            if proc:
                proc.terminate()
            db_execute("UPDATE bots SET running=0 WHERE id=?", (bot_id,), commit=True)
            watchdog_restarting.discard(bot_id)
            bot.send_message(uid, t(uid, "bot_stopped_msg"))
            add_log(bot_id, "Bot durduruldu ⏸️")

        elif action == "delete":
            with running_lock:
                proc = running_processes.pop(bot_id, None)
            if proc:
                proc.terminate()
            watchdog_restarting.discard(bot_id)
            filename, _ = get_bot_info(bot_id)
            if filename and os.path.exists(filename):
                os.remove(filename)
            db_execute("DELETE FROM bots WHERE id=?", (bot_id,), commit=True)
            bot.send_message(uid, t(uid, "file_deleted"))

        elif action == "log":
            with logs_lock:
                logs = list(bot_logs.get(bot_id, []))
            if not logs:
                bot.send_message(uid, t(uid, "no_logs"))
            else:
                log_text = t(uid, "logs_title") + "\n".join(logs[-50:])
                if len(log_text) > 4096:
                    log_text = log_text[-4096:]
                bot.send_message(uid, log_text)

# ================= DESTEK =================
@bot.message_handler(func=lambda m: m.text in [TEXTS["tr"]["btn_support"], TEXTS["en"]["btn_support"]])
def support(message):
    uid = message.from_user.id
    support_wait[uid] = True
    bot.send_message(message.chat.id, t(uid, "support_prompt"))

@bot.message_handler(func=lambda m: m.from_user.id in support_wait)
def support_msg(message):
    uid = message.from_user.id
    support_wait.pop(uid, None)
    bot.send_message(ADMIN_ID, f"📩 *Destek*\n\n👤 {message.from_user.first_name}\n🆔 {uid}\n🌐 {get_user_lang(uid).upper()}\n\n{message.text}", parse_mode="Markdown")
    bot.send_message(message.chat.id, t(uid, "support_sent"))

# ================= RUN =================
print("✅ SafeVds BOT ÇALIŞIYOR...")
bot.infinity_polling(timeout=60, long_polling_timeout=30)
