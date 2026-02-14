# Telegram Bot Setup Guide

## 1. BotFather ile Bot Oluştur

1. Telegram'da **@BotFather** ile konuşmaya başla
2. `/newbot` komutunu gönder
3. Bot adı ver: `MergenLite Monitor`
4. Username ver: `mergenlite_monitor_bot` (veya benzeri)
5. BotFather sana **API Token** verecek (şuna benzer): `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

**Bu token'ı güvenli sakla!** `.env` dosyasına ekleyeceğiz.

## 2. Chat ID Bul

Bot'undan bildirim alabilmek için senin chat ID'ni bulmak gerek:

1. Bot'unu başlat (Search → `@mergenlite_monitor_bot` → Start)
2. Bir mesaj yaz, örn: "merhaba"
3. Şu URL'yi tarayıcıda aç (TOKEN'ı değiştir):
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
4. JSON response'da şunu ara:
   ```json
   "chat": {
     "id": 987654321,  ← BU SENIN CHAT_ID'N
     "first_name": "...",
     ...
   }
   ```

## 3. .env Dosyasına Ekle

```env
# Telegram Notifications
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
TELEGRAM_ENABLED=true
```

## 4. Test Et

Bot kurulumunu test etmek için:

```bash
cd mergen/api
python -c "
from app.services.notifications import send_telegram_alert
import asyncio
asyncio.run(send_telegram_alert('INFO', 'MergenLite monitoring is active! ✅', {}))
"
```

Telegram'da bu bildirimi görmelisin! 🎉
