# Jak zdobyć REGON_API_KEY (USER_KEY do BIR1.1 GUS)

> **Cel:** Uzyskać klucz produkcyjny do REGON API (BIR1.1) i wstawić go do `REGON_API_KEY` w `.env`.

---

## 📧 Szablon emaila (wyślij na `regon_bir@stat.gov.pl`)

**Temat:** `Wniosek o klucz API do usługi BIR1 — dostęp produkcyjny`

```
Dzień dobry,

zwracam się z wnioskiem o przyznanie klucza API (USER_KEY) do usługi
„Dostęp do danych rejestrowych REGON poprzez usługę sieciową – interfejsy API"
(BIR1.1) — środowisko produkcyjne.

Dane wnioskodawcy:
- Pełna nazwa podmiotu: BILLS Sp. z o.o.
- Numer REGON: 020089511
- Imię i nazwisko osoby do kontaktu: Marceli Ciepliński
- Adres email osoby do kontaktu: marceli@bills.pl
- Numer telefonu stacjonarnego: +48 62 586 07 38
- Numer telefonu komórkowego: [TUTAJ WPISZ]
- Adresy IP, z których będą się komunikowały systemy: [TUTAJ WPISZ — stałe IP serwera lub pule adresów]
- Przewidywana łączna liczba zapytań w skali miesiąca: rząd wielkości 1 000–10 000 zapytań/miesiąc

Cel wykorzystania:
Weryfikacja i enrichment danych firm w ramach wewnętrznego projektu B2B
research dystrybucji maszyn tytoniowych (PowerMatic, Hawk). Głównie:
- wyszukiwanie firm po NIP → pobranie KRS
- walidacja adresu, formy prawnej, PKD
- potwierdzenie że firma jest aktywna

Dane będą przechowywane lokalnie, przetwarzane wyłącznie do celów
biznesowych, nie będą przekazywane osobom trzecim ani publikowane.

Zobowiązuję się do przestrzegania warunków korzystania z usługi,
w szczególności limitów zapytań (do 20 000 w godzinach szczytu 8:00-16:59).

Proszę o informację zwrotną z przyznanym kluczem oraz ewentualnymi
dodatkowymi wymaganiami (np. umowa powierzenia przetwarzania danych).

Z poważaniem,
Marceli Ciepliński
BILLS Sp. z o.o.
ul. Ignacego Daszyńskiego 31, 63-500 Ostrzeszów
```

---

## 📋 Pola obowiązkowe (z oficjalnej instrukcji GUS)

Wniosek **musi** zawierać:
1. ✅ Pełna nazwa podmiotu
2. ✅ Numer REGON podmiotu
3. ✅ Imię i nazwisko osoby do kontaktu
4. ✅ Adres email osoby do kontaktu
5. ✅ Numer telefonu stacjonarnego
6. ✅ Numer telefonu komórkowego
7. ✅ Adresy IP, z których będą się komunikować systemy
8. ✅ Przewidywana liczba zapytań w skali miesiąca (rząd wielkości)

**Adres:** `regon_bir@stat.gov.pl`
**Język:** polski (oficjalna korespondencja z GUS)

---

## 🔑 Po otrzymaniu klucza

1. **Wstaw do `.env`:**
   ```bash
   cd /Volumes/MC-BRAIN/Dev-Ext/BILLSzuka
   echo 'REGON_API_KEY=twój-klucz' >> .env
   ```

2. **Zweryfikuj że działa:**
   ```bash
   python3 tools/krs_search.py --nip 5140361901
   ```
   Oczekiwany output: lista firm z NIP, REGON, KRS, adresem, formą prawną.

3. **Jeśli nie działa:**
   - Sprawdź że klucz nie ma literówek
   - Sprawdź czy IP Twojego komputera jest w puli adresów zgłoszonych
   - Sprawdź limity (max 20 000 zapytań/h w szczycie 8-16:59, 10 000/h rano/wieczór)
   - Napisz do `regon_bir@stat.gov.pl` z opisem problemu

---

## 🔄 Klucz testowy (bez czekania na produkcyjny)

Jeśli nie chcesz czekać na klucz produkcyjny, można użyć klucza testowego
GUS (dane nieaktualne, zanonimizowane):

```python
# w .env
REGON_API_KEY=abcde12345abcde12345
```

**Ograniczenia klucza testowego:**
- Dane są stare i zanonimizowane
- Dobre tylko do testów skryptu
- Nie nadaje się do produkcyjnej weryfikacji firm

---

## 📊 Limity API (z oficjalnej dokumentacji GUS)

| Okres | Limit zapytań |
|---|---|
| 8:00-16:59 (szczyt) | do 20 000/h |
| 6:00-7:59, 17:00-21:59 | do 10 000/h |
| 22:00-5:59 | bez limitu |

Przekroczenie limitu **nie** blokuje natychmiast — GUS najpierw wysyła ostrzeżenia.
Ale w perspektywie dłuższej może zablokować.

---

## ⏰ Czas oczekiwania na klucz

Według doświadczeń innych deweloperów:
- **Klucz testowy:** natychmiast (klucz publiczny, patrz wyżej)
- **Klucz produkcyjny:** 1-7 dni roboczych (GUS to administracja publiczna)

Jeśli nie ma odpowiedzi po 7 dniach → follow-up na ten sam email.

---

## 🛠️ Alternatywy (gdyby GUS nie odpowiedział)

1. **CEIDG API (dane.biznes.gov.pl)** — mamy już token, działa dla JDG
2. **KRS API (api-krs.ms.gov.pl)** — działa bez auth, tylko lookup (nie search by name)
3. **Apify CEIDG Scraper** (https://apify.com/trev0n/ceidg-scraper) — paid, no API key
4. **nipgo.pl** — agregator 3M polskich firm, freemium
5. **Panoramafirm.pl / aleo.com / rejestr.io** — agregatory paid
6. **Web search przez DuckDuckGo/Brave** — fallback manualny

Szczegóły w `RUNBOOK.md` → "DOKUMENTY FINANSOWE I REJESTRY".
