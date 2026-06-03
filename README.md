# NEXOS

NEXOS, Render gibi platformlarda 7/24 çalışmaya uygun Python tabanlı Discord moderasyon botudur.

## Kurulum

```bash
pip install -r requirements.txt
```

Ortam değişkenlerini ayarla:

```env
DISCORD_TOKEN=bot_tokenin
GUILD_ID=sunucu_id
VOICE_CHANNEL_ID=opsiyonel_ses_kanali_id
```

Botu başlat:

```bash
python bot.py
```

`GUILD_ID` yazılırsa slash komutlar o sunucuda hemen görünür. Boş bırakılırsa global yüklenir ve Discord tarafında görünmesi zaman alabilir.

## Slash Komutlar

- `/help` komut listesini gösterir.
- `/ping` bot gecikmesini gösterir.
- `/server` sunucu bilgilerini gösterir.
- `/user` üye bilgilerini gösterir.
- `/clear` mesaj siler.
- `/kick` üyeyi atar.
- `/ban` üyeyi banlar.
- `/unban` ban kaldırır.
- `/timeout` üyeyi susturur.
- `/untimeout` susturmayı kaldırır.
- `/warn` uyarı verir.
- `/warnings` uyarıları listeler.
- `/clear-warnings` uyarıları temizler.
- `/role-add` rol verir.
- `/role-remove` rol alır.
- `/lock` kanalı kilitler.
- `/unlock` kanal kilidini açar.
- `/slowmode` yavaş modu ayarlar.
- `/say` bot adına mesaj gönderir.
- `/embed` embed mesaj gönderir.
- `/kurulum` temel sunucu kanal kurulumunu yapar.

## Discord Developer Portal

Botun düzgün çalışması için şu intentleri aç:

- Server Members Intent
- Message Content Intent

Moderasyon komutları için bot rolünü, işlem yapacağı üyelerin rollerinden daha yukarı taşı.
