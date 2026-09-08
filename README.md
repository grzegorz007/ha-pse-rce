# PSE RCE Price Chain dla Home Assistant

Integracja pobiera Rynkowe Ceny Energii (RCE) bezpośrednio z oficjalnego API **PSE (Polskie Sieci Elektroenergetyczne)** i przygotowuje gotowy wektor cenowy idealny do współpracy z **EMHASS** oraz systemami optymalizacji energii (np. GoodWe EMS).

## Funkcje
- **Automatyczna synchronizacja czasu:** Dopasowuje ceny do siatki 30-minutowej startującej od bieżącego slotu lub od północy.
- **Inteligentny fallback (Rollover 24h):** Jeśli PSE nie opublikowało jeszcze stawek na kolejny dzień, integracja automatycznie uzupełnia brakujące dane, powtarzając profil cenowy z poprzedniej doby (zapobiega to błędom solvera).
- **Przelicznik jednostek:** Automatycznie konwertuje stawki z PLN/MWh na PLN/kWh.
- **Konfiguracja z poziomu UI:** Możliwość zmiany horyzontu (np. 96 kroków dla 48h) w opcjach integracji.

## Instalacja przez HACS
1. Dodaj to repozytorium jako niestandardowe repozytorium niestandardowe (Custom Repository) w HACS (typ: Integracja).
2. Wyszukaj **PSE RCE Price Chain** i zainstaluj.
3. Zrestartuj Home Assistant i dodaj integrację w panelu Urządzenia i Usługi.