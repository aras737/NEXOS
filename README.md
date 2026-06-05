# NEXOS

NEXOS, Render uzerinde 7/24 calismaya uygun Python tabanli slash moderasyon botudur.

## Render

Render Environment alaninda bu degerler bulunmali:

```env
DISCORD_TOKEN=bot_tokenin
GUILD_ID=sunucu_id
VOICE_CHANNEL_ID=opsiyonel_ses_kanali_id
MEMBER_COUNT_CHANNEL_ID=1511798754980663492
LOG_CHANNEL_ID=opsiyonel_log_kanali_id
NEXOS_DATA_DIR=/var/data/nexos
```

`DISCORD_TOKEN` repoya yazilmaz. Render'da env olarak kalir.

`GUILD_ID` yazilirsa slash komutlar o sunucuda hemen gorunur. Bos birakilirsa global yuklenir ve Discord tarafinda gorunmesi zaman alabilir.

Uyari verileri `NEXOS_DATA_DIR/warnings.json`, ekonomi verileri `NEXOS_DATA_DIR/economy.json` dosyasinda tutulur. Render'da restart/deploy sonrasi kaybolmamasi icin persistent disk `/var/data` olarak mount edilmelidir. Bu repo icindeki `render.yaml` bunun icin `nexos-data` diskini ve `NEXOS_DATA_DIR=/var/data/nexos` ayarini tanimlar.

`MEMBER_COUNT_CHANNEL_ID` verilen kanal adini otomatik `uyeler-<sayi>` formatinda gunceller. Botun Manage Channels yetkisi olmalidir.

`LOG_CHANNEL_ID` opsiyoneldir. Bos birakirsan `/set-log-channel` komutu ile Discord icinden ayarlayabilirsin. Log ayari persistent diske yazilir.

## Lokal Calistirma

```bash
pip install -r requirements.txt
python bot.py
```

## Dosya Yapisi

- `bot.py` botu baslatir, komutlari senkronlar.
- `bot_commands/` her slash komut icin ayri dosya icerir.
- `core/` ortak config, hata, embed, storage ve yetki yardimcilarini icerir.
- `render.yaml` Render build/start ayarlarini icerir.
- `warnings.json`, `economy.json`, `settings.json` ve `logs.jsonl` repoya yazilmaz; Render disk altinda saklanir.

## Slash Komutlar

- `/help` komut listesini gosterir.
- `/invite` bot davet linkini ve gerekli yetkileri gosterir.
- `/set-log-channel` log kanalini ayarlar. Yetki: Administrator.
- `/ping` bot gecikmesini gosterir.
- `/server` sunucu bilgilerini gosterir.
- `/user` uye bilgilerini gosterir.
- `/balance` ekonomi bakiyesini gosterir.
- `/daily` gunluk ekonomi odulunu alir.
- `/work` calisip kredi kazanir.
- `/deposit` cuzdandaki parayi bankaya yatirir.
- `/withdraw` bankadaki parayi cuzdana ceker.
- `/pay` baska uyeye para gonderir.
- `/leaderboard` ekonomi liderlik tablosunu gosterir.
- `/clear` mesaj siler. Yetki: Manage Messages.
- `/kick` uyeyi atar. Yetki: Kick Members.
- `/ban` uyeyi banlar. Yetki: Ban Members.
- `/unban` ban kaldirir. Yetki: Ban Members.
- `/timeout` uyeyi susturur. Yetki: Moderate Members.
- `/untimeout` susturmayi kaldirir. Yetki: Moderate Members.
- `/warn` uyari verir. Yetki: Moderate Members.
- `/warnings` uyarilari listeler. Yetki: Moderate Members.
- `/clear-warnings` uyarilari temizler. Yetki: Moderate Members.
- `/role-add` rol verir. Yetki: Manage Roles.
- `/role-remove` rol alir. Yetki: Manage Roles.
- `/lock` kanali kilitler. Yetki: Manage Channels.
- `/unlock` kanal kilidini acar. Yetki: Manage Channels.
- `/slowmode` yavas modu ayarlar. Yetki: Manage Channels.
- `/say` bot adina mesaj gonderir. Sadece sunucu sahibi.
- `/embed` embed mesaj gonderir. Yetki: Manage Messages.
- `/kurulum` temel kanal kurulumunu yapar. Yetki: Administrator.

## Hata Bildirimi

Bir slash komut hata verirse bot komutu kullanan kisiye DM atar. DM icinde komut adi, gercek hata mesaji, komut dosyasi ve hatanin geldigi dosya/satir bilgisi bulunur.

Log sistemi sunlari kaydeder:

- Komut kullanimlari
- Komut hatalari
- Uye giris/cikis
- Bot baslatma
- `/say` kullanimlari ve reddedilen denemeler

Loglar hem `NEXOS_DATA_DIR/logs.jsonl` dosyasina yazilir hem de ayarlanmis log kanalina embed olarak gonderilir.

## Discord Developer Portal

Botun duzgun calismasi icin su intentleri ac:

- Server Members Intent

Moderasyon komutlari icin bot rolunu, islem yapacagi uyelerin rollerinden daha yukari tasi.

## Bot Davet Yetkileri

Botu `/invite` komutunun verdigi linkle yeniden davet edebilirsin. Link su yetkileri ister:

- View Channels
- Send Messages
- Embed Links
- Read Message History
- Use Application Commands
- Manage Messages
- Manage Channels
- Manage Roles
- Kick Members
- Ban Members
- Moderate Members
- Connect
- Speak

Permission bit degeri: `1101930785814`
