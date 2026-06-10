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
YOUTUBE_COOKIES=opsiyonel_youtube_cookies_txt_veya_base64
NEXOS_DATA_DIR=/var/data/nexos
```

`DISCORD_TOKEN` repoya yazilmaz. Render'da env olarak kalir.

`GUILD_ID` yazilirsa slash komutlar o sunucuda hemen gorunur. Bos birakilirsa global yuklenir ve Discord tarafinda gorunmesi zaman alabilir.

Uyari verileri `NEXOS_DATA_DIR/warnings.json`, ekonomi verileri `NEXOS_DATA_DIR/economy.json`, cekilis verileri `NEXOS_DATA_DIR/giveaways.json`, kayit verileri `NEXOS_DATA_DIR/registrations.json` dosyasinda tutulur. Render'da restart/deploy sonrasi kaybolmamasi icin persistent disk `/var/data` olarak mount edilmelidir. Bu repo icindeki `render.yaml` bunun icin `nexos-data` diskini ve `NEXOS_DATA_DIR=/var/data/nexos` ayarini tanimlar.

`MEMBER_COUNT_CHANNEL_ID` verilen kanal adini otomatik `uyeler-<sayi>` formatinda gunceller. Botun Manage Channels yetkisi olmalidir.

`LOG_CHANNEL_ID` opsiyoneldir. Bos birakirsan `/set-log-channel` komutu ile Discord icinden ayarlayabilirsin. Log ayari persistent diske yazilir. Ozel log kanallari icin bot `log`, `mesaj-log`, `ses-log`, `mod-log`, `giris-cikis-log`, `ceza-log` kanal isimlerini otomatik tanir.

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
- `giveaways.json` aktif ve bitmis cekilisleri saklar; restart sonrasi cekilisler devam eder.
- `registrations.json` son kayitlari ve kayit gecmisini saklar.
- Hos geldin karti icin `Pillow` kullanilir. Paket Render build sirasinda `requirements.txt` ile kurulur.
- Muzik sistemi icin `yt-dlp` ve Python paketli `ffmpeg` destegi kullanilir. Paketler Render build sirasinda `requirements.txt` ile kurulur.
- Voice welcome ses dosyalari URL olarak verilebilir veya Render diskinde `NEXOS_DATA_DIR/sounds/` altinda tutulabilir; repo icine yazilmaz.
- YouTube `Sign in to confirm you're not a bot` hatasi verirse Render Environment alanina `YOUTUBE_COOKIES` eklenir. Deger Netscape `cookies.txt` icerigi veya `base64:` ile baslayan base64 hali olabilir. Alternatif olarak `YOUTUBE_COOKIES_FILE` ile Render diskindeki cookie dosyasi yolu verilebilir.

## Slash Komutlar

- `/help` komut listesini gosterir.
- `/invite` bot davet linkini ve gerekli yetkileri gosterir.
- `/set-log-channel` genel/mesaj/ses/mod/giris-cikis/ceza log kanalini ayarlar. Yetki: Administrator.
- `/last-actions` botun kaydettigi son islemleri gosterir. Yetki: Administrator.
- `/set-auto-role` yeni gelenlere otomatik rol ayarlar. Yetki: Administrator.
- `/welcome-settings` giris-cikis kanali ve galaksi hos geldin/cikis mesajlarini ayarlar. Yetki: Administrator.
- `/role-panel` butona tiklayanlara rol veren paneli gonderir. Yetki: Administrator.
- `/automod-settings` davet/link/spam/etiket AutoMod ayarlarini yapar. Yetki: Administrator.
- `/automod-word-add` yasak kelime ekler. Yetki: Administrator.
- `/automod-word-remove` yasak kelime siler. Yetki: Administrator.
- `/automod-info` AutoMod ayarlarini gosterir. Yetki: Administrator.
- `/security-settings` bot ekleme korumasi ve anti-raid ayarlarini yapar. Yetki: Administrator.
- `/security-allow-bot` izinli bot listesine bot ID ekler. Yetki: Administrator.
- `/security-deny-bot` izinli bot listesinden bot ID siler. Yetki: Administrator.
- `/security-info` sunucu koruma ayarlarini gosterir. Yetki: Administrator.
- `/register-settings` `Isim | Yas` formatli kayit kanalini ve yas rol sistemini ayarlar. Yetki: Administrator.
- `/register-panel` kayit format panelini gonderir. Yetki: Administrator.
- `/ping` bot gecikmesini gosterir.
- `/server` sunucu bilgilerini gosterir.
- `/user` uye bilgilerini gosterir.
- `/profile` ozel NEXOS profil kartini gosterir.
- `/avatar` uye avatarini gosterir.
- `/botinfo` bot sistem bilgisini gosterir.
- `/balance` ekonomi bakiyesini gosterir.
- `/daily` gunluk ekonomi odulunu alir.
- `/work` calisip kredi kazanir.
- `/deposit` cuzdandaki parayi bankaya yatirir.
- `/withdraw` bankadaki parayi cuzdana ceker.
- `/pay` baska uyeye para gonderir.
- `/leaderboard` ekonomi liderlik tablosunu gosterir.
- `/giveaway-start` butonlu cekilis baslatir. Yetki: Manage Server.
- `/giveaway-end` aktif cekilisi hemen bitirir. Yetki: Manage Server.
- `/giveaway-reroll` bitmis cekilis icin yeni kazanan secer. Yetki: Manage Server.
- `/giveaway-cancel` aktif cekilisi iptal eder. Yetki: Manage Server.
- `/giveaway-list` aktif cekilisleri listeler. Yetki: Manage Server.
- `/music-play` ses kanalinda muzik acar veya siraya ekler. Yetki: Administrator.
- `/music-skip` calan muzigi atlar. Yetki: Administrator.
- `/music-stop` muzigi durdurur ve sirayi temizler. Yetki: Administrator.
- `/music-pause` muzigi duraklatir. Yetki: Administrator.
- `/music-resume` muzigi devam ettirir. Yetki: Administrator.
- `/music-leave` botu ses kanalindan cikarir. Yetki: Administrator.
- `/music-now` calan muzigi ve sira sayisini gosterir. Yetki: Administrator.
- `/voice-welcome-settings` ses kanalina girislerde calacak welcome/staff sesini ayarlar. Yetki: Administrator.
- `/voice-welcome-info` voice welcome ayarlarini gosterir. Yetki: Administrator.
- `/eco-add` yetkili olarak kredi ekler. Yetki: Administrator.
- `/eco-remove` yetkili olarak kredi siler. Yetki: Administrator.
- `/eco-set` yetkili olarak bakiyeyi ayarlar. Yetki: Administrator.
- `/eco-reset` yetkili olarak ekonomi hesabini sifirlar. Yetki: Administrator.
- `/ticket-panel` panel-only ticket sistemini gonderir. Yetki: Administrator. Opsiyonel `channel`, `support_role` ve `category` ayarlari alir.
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

## AutoMod Sistemi

AutoMod varsayilan olarak aciktir; Administrator, Manage Messages veya Moderate Members yetkili uyeleri es gecer. Davet linki, spam, cok etiket ve yasak kelime olaylarini yakalar. Normal link engeli varsayilan olarak kapalidir; istenirse acilir.

Ornek:

```text
/automod-settings enabled:true anti_invite:true anti_links:false anti_spam:true anti_mass_mention:true action:Timeout timeout_minutes:10
/automod-word-add word:yasak_kelime
```

Aksiyonlar:

- `Sil`: Mesaji siler ve loglar.
- `Uyar`: Mesaji siler, uyari kaydeder ve loglar.
- `Timeout`: Mesaji siler, uyari kaydeder, uyeyi timeout atmaya calisir ve loglar.

## Sunucu Koruma ve Bot Guard

Bot ekleme korumasi varsayilan olarak aciktir. Sunucuya allowlist disi bir bot eklenirse NEXOS audit logdan ekleyeni bulmaya calisir, eklenen botu atar, ekleyenin tehlikeli yetkili rollerini almaya calisir ve sunucu sahibine DM ile Onayla/Reddet/Yetki Al butonlu embed gonderir.

Sunucu sahibi DM panelinde `Onayla` derse bot ID'si allowlist'e girer; ayni bot tekrar eklenirse izinli sayilir.

Ornek:

```text
/security-settings enabled:true bot_guard_enabled:true anti_raid_enabled:true raid_threshold:3 raid_window_seconds:30
/security-allow-bot bot_id:123456789012345678
```

Anti-raid sistemi kisa surede cok kanal/rol silme/olusturma, ban ve kick hareketlerini izler. Esik asilinca islemi yapan uyenin Administrator, Manage Server, Manage Roles, Manage Channels, Ban/Kick/Moderate Members gibi tehlikeli rollerini almaya calisir, `mod-log` kanalina ve sunucu sahibine alarm gonderir.

## Ticket Sistemi

Ticketler sadece `/ticket-panel` ile gonderilen paneldeki **Ticket Ac** butonundan acilir. Ayrica ayri ticket slash komutu bulunmaz.

Panelden acilan her ticket kanalinda kontrol paneli otomatik gelir:

- `Ustlen` yetkilinin ticketi sahiplenmesini saglar.
- `Bilgi` ticket sahibi, konu, oncelik, eklenen uyeler ve detayi gosterir.
- `Transcript` son mesajlarin dosya dokumunu olusturur.
- `Uye Ekle` ve `Uye Cikar` yetkilinin ID/etiket ile erisimi yonetmesini saglar.
- `Yeniden Adlandir` ticket kanal adini duzenler.
- `Oncelik degistir` secimi ticket onceligini Dusuk, Normal, Yuksek veya Acil yapar.
- `Ticket Kapat` ticket sahibi veya yetkilinin sebep girerek kanali kapatmasini saglar.

Ticket yetkilisi olmak icin `Manage Channels` yetkisi yeterlidir. Istersen `/ticket-panel support_role:@rol` ile destek rolunu da ayarlayabilirsin. Kategori icin `/ticket-panel category:kategori` kullanilir.

## Cekilis Sistemi

`/giveaway-start` komutu butonlu cekilis baslatir. Sure `10m`, `1h`, `2d`, `1w` formatinda yazilir. Cekilisler `giveaways.json` dosyasina kaydedilir, bot restart yesede aktif cekilisler 30 saniyede bir kontrol edilip zamani gelince otomatik bitirilir.

Ornek:

```text
/giveaway-start prize:Nitro duration:1h winners:1 channel:#cekilis description:Family cekilisi
```

Cekilis ozellikleri:

- Katilim butonla yapilir.
- Botlar cekilise katilamaz.
- Istenirse `required_role` ile sadece belirli role sahip uyeler katilir.
- Kazananlar otomatik secilir ve kanal mesajina yazilir.
- `/giveaway-end` cekilisi hemen bitirir.
- `/giveaway-reroll` bitmis cekiliste yeni kazanan secer.
- `/giveaway-cancel` aktif cekilisi iptal eder.
- `/giveaway-list` aktif cekilisleri gosterir.
- Baslatma, katilim, bitirme, reroll, iptal ve hata durumlari loglanir.

## Kayit Sistemi

Kayit kanali `/register-settings channel:#kayit` ile ayarlanir. Ayar yapilmazsa bot adi `kayit` iceren kanallari otomatik dinler. Uye bu kanala:

```text
Ada | 16
```

formatinda yazarsa bot:

- `Ada` degerini uyenin takma adi yapar.
- `16`, `16 Yas`, `16+` gibi yas rolunu bulup verir.
- Yas rolu yoksa varsayilan olarak `16 Yas` rolunu olusturur.
- Sunucuda `Uye`, `Kayitli`, `Member` veya `Registered` rolu varsa onu da verir. Istersen `/register-settings registered_role:@rol` ile net rol secilir.
- Yanlis format, rol/nick hatasi, basarili veya kismi basarili her kayit loglanir.
- Son kayitlar `registrations.json` dosyasinda saklanir.

Panel gondermek icin:

```text
/register-panel channel:#kayit
```

## Muzik Sistemi

Muzik komutlari sadece Administrator yetkisi olan uyeler tarafindan kullanilir. Komutu kullanan yetkili once bir ses kanalina girer, sonra:

```text
/music-play query:şarkı adı veya YouTube linki
```

komutunu kullanir. Bot ses kanalina girer, sarki caliyorsa yeni istegi siraya ekler.

Muzik komutlari:

- `/music-play` sarki acar veya siraya ekler.
- `/music-skip` calan sarkiyi atlar.
- `/music-stop` muzigi durdurur ve sirayi temizler.
- `/music-pause` muzigi duraklatir.
- `/music-resume` duraklatilan muzigi devam ettirir.
- `/music-leave` botu ses kanalindan cikarir.
- `/music-now` calan sarkiyi ve sira sayisini gosterir.

Muzik acma, siraya ekleme, baslama, skip, stop, pause, resume, leave ve hata durumlari `ses-log` tarafina kaydedilir.

YouTube bazen Render IP adreslerinden gelen istekleri bot dogrulamasina sokabilir. Bu durumda bot `YOUTUBE_COOKIES` ayari ister. Cookie ayari yoksa bot artik ses kanalina girip sessiz kalmaz; once sarki kaynagini almaya calisir, kaynak alinamazsa komutu kullanan yetkiliye net hata mesaji verir.

## Voice Welcome Sistemi

`thearkxd/discord-welcome-bots` reposundaki mantiga benzer sekilde NEXOS belirlenen ses kanalini dinleyebilir. Uye kanala girdiginde ayarlanan welcome sesi calar; yetkili rol ve kayitsiz rol ayarlanirsa yetkili/kayitsiz bulusmasi icin ayri staff sesi de calabilir.

Ornek:

```text
/voice-welcome-settings channel:"Kayit Bekleme" welcome_sound:https://site.com/welcome.mp3 staff_sound:https://site.com/staff.mp3 staff_role:@Yetkili unregistered_role:@Kayitsiz enabled:true
```

Davranis:

- `channel` ayarlanmazsa `VOICE_CHANNEL_ID` varsa onu kullanir.
- `unregistered_role` ayarlanirsa sadece o role sahip uyeler tetikler; ayarlanmazsa bot olmayan herkes sayilir.
- `staff_role` ve `staff_sound` ayarliyken kanalda ilk yetkili ve ilk kayitsiz ayni anda bulusursa staff sesi calar.
- Bot baska muzik veya ses caliyorsa voice welcome sesi atlanir ve `ses-log` kanalina yazilir.
- Hata, atlama, ses kaynagi eksigi ve basarili calisma olaylari loglanir.

## Giris-Cikis ve Rol Paneli

`/welcome-settings` komutu giris-cikis kanalini ve NEXOS galaksi temasindaki mesajlari ayarlar. Giris mesajlarinda uye avatari, sunucu adi ve uye sayisi bulunan PNG welcome karti otomatik gonderilir. Mesajlarda su degiskenler kullanilabilir:

- `{mention}` uye etiketini yazar.
- `{user}` kullanici adini yazar.
- `{name}` sunucudaki gorunen adi yazar.
- `{server}` sunucu adini yazar.
- `{count}` guncel uye sayisini yazar.

Ornek:

```text
/welcome-settings welcome_channel:#hosgeldin leave_channel:#giris-cikis welcome_message:{mention}, NEXOS galaksisine hos geldin. Artik {count}. uyemizsin.
```

`/set-auto-role` yeni gelen uyelere otomatik rol verir. `/role-panel` ise secilen kanala butonlu rol alma paneli gonderir; butona tiklayan uye ayarlanan rolu alir.

Rol sistemlerinde rol sirasi ve guvenlik kontrolu vardir:

- Botun rolu verilecek rolden yukarida olmalidir.
- Komutu kullanan yetkilinin rolu verilecek rolden yukarida olmalidir.
- Butonla alinacak rol Administrator, Manage Roles, Manage Channels, Ban/Kick/Moderate Members gibi tehlikeli yetkilere sahip olamaz.
- @everyone ve entegrasyon/bot tarafindan yonetilen roller kullanilamaz.

## Hata Bildirimi

Bir slash komut hata verirse bot komutu kullanan kisiye DM atar. DM icinde komut adi, gercek hata mesaji, komut dosyasi ve hatanin geldigi dosya/satir bilgisi bulunur.

Log sistemi sunlari kaydeder:

- Komut kullanimlari
- Komut hatalari
- AutoMod davet/link/spam/etiket/yasak kelime yakalamalari
- Izinsiz bot ekleme, bot allowlist onayi/reddi ve yetki alma denemeleri
- Anti-raid kanal/rol/ban/kick alarmlari
- Uye giris/cikis
- Uye isim, rol ve timeout durumu degisiklikleri
- Mesaj silme ve mesaj duzenleme
- Kanal olusturma, silme ve ayar degisiklikleri
- Rol olusturma, silme, isim/renk/yetki degisiklikleri
- Ses kanalina girme, cikma, kanal degistirme, mute/deaf/kamera/yayin durumu
- Ban ve ban kaldirma
- Sunucu emoji ekleme, silme ve ad degistirme
- Galaksi hos geldin/cikis mesaj ayarlari
- Bot baslatma
- Botun sunucu sayisi ve toplam kullanici sayisi
- `/say` kullanimlari ve reddedilen denemeler
- Ticket acma/kapatma
- Ticket claim, uye ekle/cikar, oncelik, transcript, isim degistirme
- Cekilis baslatma, katilim, bitirme, reroll, iptal ve hata durumlari
- Kayit basarili/kismi basarili/hata, yas rolu olusturma ve nick degisimi
- Muzik acma, siraya ekleme, baslama, atlama, durdurma, duraklatma, devam ettirme, ayrilma ve hata
- Voice welcome sesi calinmasi, atlanmasi ve hata durumlari
- Oto rol verme/hata ve buton rol verme/hata
- Ban/kick/timeout/warn/rol/kanal moderasyon islemleri

Loglar hem `NEXOS_DATA_DIR/logs.jsonl` dosyasina yazilir hem de ayarlanmis log kanalina embed olarak gonderilir. Bot ayrica son aksiyonu `NEXOS_DATA_DIR/last_actions.json` dosyasina kaydeder; `/last-actions` ile son genel islem veya kategori bazli son islem gorulebilir.

Ozel log kanal eslesmeleri:

- `log`: genel bot ve komut loglari.
- `mesaj-log`: mesaj silme ve mesaj duzenleme.
- `ses-log`: ses kanalina girme/cikma, kanal degistirme, mute/deaf/kamera/yayin ve muzik.
- `mod-log`: kanal, rol, ticket, cekilis, AutoMod, sunucu koruma, bot guard, emoji, oto rol ve yonetim degisiklikleri.
- `giris-cikis-log`: uye giris-cikis, kayit ve uye isim degisiklikleri.
- `ceza-log`: AutoMod engelleri, ban, unban, timeout, warn, kick ve ceza tarafi.

Kanal isimlerinde emoji veya ayirici olabilir; `💬・mesaj-log` gibi isimler de taninir. Elle ayarlamak icin:

```text
/set-log-channel channel:#mesaj-log log_type:Mesaj Log
/set-log-channel channel:#ses-log log_type:Ses Log
/set-log-channel channel:#mod-log log_type:Mod Log
/set-log-channel channel:#giris-cikis-log log_type:Giris-Cikis Log
/set-log-channel channel:#ceza-log log_type:Ceza Log
```

## Discord Developer Portal

Botun duzgun calismasi icin su intentleri ac:

- Server Members Intent
- Message Content Intent

Mesaj silme/duzenleme loglarinda mesaj icerigini gorebilmek icin Message Content Intent acik olmalidir. Kapali olursa bot yine olaylari loglar, fakat mesaj icerigi bos gelebilir.

Moderasyon komutlari icin bot rolunu, islem yapacagi uyelerin rollerinden daha yukari tasi.

## Bot Davet Yetkileri

Botu `/invite` komutunun verdigi linkle yeniden davet edebilirsin. Link su yetkileri ister:

- View Channels
- View Audit Log
- Send Messages
- Embed Links
- Read Message History
- Use Application Commands
- Manage Messages
- Manage Channels
- Manage Roles
- Manage Nicknames
- Kick Members
- Ban Members
- Moderate Members
- Connect
- Speak
- Use Voice Activity

Permission bit degeri: `1102098558102`
