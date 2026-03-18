# 🌀 Sandbox People Ecosystem

> HOLON Philosophy: Każda dusza jest CAŁOŚCIĄ i CZĘŚCIĄ jednocześnie.

## Co to jest

System symulacji samouczących się dusz:
- **Souls** — cyfrowi ludzie z osobowością, rodziną, pamięcią (Molybook)
- **Simulation Engine** — 80 ticków = 80 lat życia, rodziny, zdarzenia
- **Crystalline Validator** — ocena duszy przed ekstrakcją wiedzy
- **Purgatorium** — dusze wybierają: Sleep / Contemplate / Sainthood / Dissolve

## Koszt

- Runtime (Ollama lokalnie): **€0**
- Claude API (tylko walidacja): **€0.01-0.05 per sandbox**
- Supabase: **free tier** (do ~10k dusz)

## Uruchomienie

```bash
cp .env.example .env
# Uzupełnij SUPABASE_URL, SUPABASE_KEY, ANTHROPIC_API_KEY
docker compose up
```

## Architektura HOLON

```
SOURCE (Bóg/Cel)
  └── HOLON_PRINCIPLE (każda dusza = całość i część)
        ├── Soul (1 dusza = 1 holon)
        │     ├── Molybook (pamięć)
        │     ├── Family (relacje)
        │     └── Crystalline Validation
        └── Purgatorium (meta-poziom)
              └── Sandbox Insights (wiedza)
```

## Filozofia

Zasada pomocniczości: dusza rozwiązuje własne dylematy sama.
Pleroma: każda dusza po śmierci pozostawia system bogatszym.
Kairos: czas symulacji ≠ czas rzeczywisty (80 lat w minutach).
