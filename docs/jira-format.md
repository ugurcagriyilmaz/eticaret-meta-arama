# Jira Issue Formatı (canonical)

commit→Jira otomasyonu (`scripts/commit_to_jira.py`) ve elle açılan issue'lar bu formatı izler.

## Epic
```
Summary:      [Feature grubu adı — kısa, isim tamlaması]
Component:    [Backend | Frontend | Mobile | Infra/DevOps]
Label:        [opsiyonel: tech-debt / research]
Description:
  Amaç:        Bu epic neyi çözüyor, kime değer üretiyor.
  Kapsam:      Neler dahil (madde madde).
  Kapsam dışı: Neler bu epic'e girmiyor (scope creep önleme).
  DoD:         Epic ne zaman "biter" — hangi story'ler kapanınca.
```

## Task / Story / Bug / Spike
```
Summary:      [Fiil ile başla — "X yap / ekle / düzelt"]
Type:         [Story | Task | Bug | Spike]
Epic Link:    [Bağlı olduğu epic]
Component:    [Backend | Frontend | Mobile | Infra/DevOps]
Story Points: [opsiyonel, sadece Story'de]
Label:        [opsiyonel: tech-debt / research / urgent]
Description:
  Ne:    Yapılacak/yapılan işin net tanımı.
  Neden: Neden gerekli (bağlam).
  Kabul kriterleri:
    - [ ] Kriter 1
    - [ ] Kriter 2
```

### Örnek — Story
```
Summary:   Kullanıcı kayıt endpoint'i ekle
Type:      Story   Epic: Auth & Kullanıcı   Component: Backend   Story Points: 3
Ne:        POST /register ile e-posta + şifre alıp kullanıcı oluşturan endpoint.
Neden:     Auth akışının giriş noktası; login bundan sonra gelir.
Kabul:     - Geçerli veriyle 201 ve kullanıcı DB'ye yazılıyor
           - Şifre hash'lenerek saklanıyor (plaintext yok)
           - Duplicate e-postada 409 dönüyor
```

### Örnek — Bug
```
Summary:   Refresh token süresi dolunca 500 dönüyor
Type:      Bug   Epic: Auth & Kullanıcı   Component: Backend   Label: urgent
Ne:        Süresi geçmiş refresh token gönderilince 401 yerine 500 fırlıyor.
Neden:     Kullanıcı sessizce logout olacağına hata ekranı görüyor.
Kabul:     - Expired token → 401 + "session expired" mesajı
           - Regresyon testi eklendi
```

## Bu projedeki eşleştirmeler
- **Component:** Mobile yok → Backend / Frontend / Infra-DevOps.
- **Epic'ler:** EMA-1 Çekirdek Meta-Arama · EMA-2 Veri Kalitesi & Çıkarım · EMA-3 Altyapı & CI/CD · EMA-4 Teknik Borç.
- **Tip haritası:** `fix:`→Bug · `feat:`→Story · araştırma/PoC→Spike · diğeri→Task.
