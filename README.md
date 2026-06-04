# NEXOS

NEXOS, Render uzerinde 7/24 calismaya uygun Python tabanli slash moderasyon botudur.

## Render

Render Environment alaninda bu degerler bulunmali:

```env
DISCORD_TOKEN=bot_tokenin
GUILD_ID=sunucu_id
VOICE_CHANNEL_ID=opsiyonel_ses_kanali_id
NEXOS_DATA_DIR=/var/data/nexos
```

`DISCORD_TOKEN` repoya yazilmaz. Render'da env olarak kalir.

`GUILD_ID` yazilirsa slash komutlar o sunucuda hemen gorunur. Bos birakilirsa global yuklenir ve Discord tarafinda gorunmesi zaman alabilir.

Uyari verileri `NEXOS_DATA_DIR/warnings.json` dosyasinda tutulur. Render'da restart/deploy sonrasi kaybolmamasi icin persistent disk `/var/data` olarak mount edilmelidir. Bu repo icindeki `render.yaml` bunun icin `nexos-data` diskini ve `NEXOS_DATA_DIR=/var/data/nexos` ayarini tanimlar.

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
- `warnings.json` repoya yazilmaz; Render disk altinda saklanir.

## Slash Komutlar

- `/help` komut listesini gosterir.
- `/ping` bot gecikmesini gosterir.
- `/server` sunucu bilgilerini gosterir.
- `/user` uye bilgilerini gosterir.
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
- `/say` bot adina mesaj gonderir. Yetki: Manage Messages.
- `/embed` embed mesaj gonderir. Yetki: Manage Messages.
- `/kurulum` temel kanal kurulumunu yapar. Yetki: Administrator.

## Hata Bildirimi

Bir slash komut hata verirse bot komutu kullanan kisiye DM atar. DM icinde komut adi, hata mesaji, komut dosyasi ve hatanin geldigi dosya/satir bilgisi bulunur.

## Discord Developer Portal

Botun duzgun calismasi icin su intentleri ac:

- Server Members Intent

Moderasyon komutlari icin bot rolunu, islem yapacagi uyelerin rollerinden daha yukari tasi.
