#!/usr/bin/env python3
"""
Sandbox Souls — Daemon Engine v1.2
Używa Anthropic Haiku zamiast Ollamy (działa bez lokalnego modelu)
Działa jako long-running service, uruchamia sandbox co CHECK_INTERVAL sekund
"""
import asyncio, json, random, hashlib, os, logging
from datetime import datetime
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SANDBOX] %(message)s")
log = logging.getLogger("sandbox")

SUPABASE_URL    = os.environ.get("SUPABASE_URL", "https://blgdhfcosqjzrutncbbr.supabase.co")
SUPABASE_KEY    = os.environ.get("SUPABASE_KEY", "")
ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
POPULATION      = int(os.environ.get("POPULATION", "20"))
TICKS           = int(os.environ.get("TICKS", "10"))
CHECK_INTERVAL  = int(os.environ.get("CHECK_INTERVAL", "3600"))  # co godzinę nowy sandbox
LLM_EVERY_N     = int(os.environ.get("LLM_EVERY_N", "5"))        # pytaj AI co N ticków

PERSONALITIES = ["curious", "empathetic", "ambitious", "spiritual", "pragmatic", "creative", "loyal"]
OCCUPATIONS   = ["farmer", "teacher", "merchant", "healer", "artist", "leader", "craftsman"]

async def sb_insert(table: str, data: dict):
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                f"{SUPABASE_URL}/rest/v1/{table}",
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                         "Content-Type": "application/json", "Prefer": "return=minimal"},
                json=data)
            return r.status_code < 300
    except Exception as ex:
        log.warning(f"Insert {table}: {ex}")
        return False

async def sb_rpc(func: str, params: dict):
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                f"{SUPABASE_URL}/rest/v1/rpc/{func}",
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                         "Content-Type": "application/json"},
                json=params)
            return r.json()
    except Exception as ex:
        log.warning(f"RPC {func}: {ex}")
        return {}

async def ask_claude(prompt: str) -> str:
    """Anthropic Haiku — tani, szybki, działa bez lokalnego GPU"""
    if not ANTHROPIC_KEY:
        return random.choice(["Działam zgodnie z sumieniem.", "Pomagam bliskim.", "Kontempluję."])
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 60,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            if r.status_code == 200:
                return r.json()["content"][0]["text"][:200]
    except Exception as ex:
        log.warning(f"Claude API: {ex}")
    return random.choice(["Działam zgodnie z sumieniem.", "Pomagam bliskim.", "Kontempluję."])

async def run_sandbox():
    sandbox_id = f"sb_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log.info(f"🌀 Starting sandbox {sandbox_id} | pop={POPULATION} ticks={TICKS}")

    await sb_insert("sandboxes", {
        "sandbox_id": sandbox_id,
        "name": f"Sandbox {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        "population_size": POPULATION,
        "status": "running"
    })

    # Spawn souls
    souls = []
    for i in range(POPULATION):
        traits = random.sample(PERSONALITIES, 2)
        soul = {
            "soul_id": f"s_{sandbox_id}_{i:04d}",
            "sandbox_id": sandbox_id,
            "name": f"Soul_{i+1:04d}",
            "age": random.randint(5, 25),
            "occupation": random.choice(OCCUPATIONS),
            "personality": {"traits": traits},
            "integrity": random.uniform(0.4, 0.9),
            "wisdom": 0.0,
            "family_id": f"fam_{sandbox_id}_{i//4}",
            "molybook": [],
            "alive": True
        }
        souls.append(soul)
        await sb_rpc("spawn_soul", {
            "p_sandbox_id": sandbox_id,
            "p_name": soul["name"],
            "p_personality": soul["personality"],
            "p_family_id": soul["family_id"]
        })
    log.info(f"  Spawned {len(souls)} souls")

    events = [
        "muszę zdecydować czy pomóc obcej osobie",
        "napotykam dylemat moralny",
        "ktoś z rodziny potrzebuje pomocy",
        "odkrywam coś nowego o sobie",
        "spotykam mędrcę który zmienia mój pogląd",
        "muszę wybrać między własnym interesem a dobrem wspólnym",
        "widzę niesprawiedliwość — czy reaguję?"
    ]

    for tick in range(TICKS):
        alive = [s for s in souls if s["alive"]]
        if tick % 5 == 0:
            log.info(f"  Tick {tick}/{TICKS}: {len(alive)} alive")

        for soul in alive:
            soul["age"] += 1
            if soul["age"] > 80 and random.random() < 0.2:
                soul["alive"] = False
                await sb_rpc("send_to_purgatorium", {
                    "p_soul_id": soul["soul_id"],
                    "p_life_summary": f"{soul['name']} żył/a {soul['age']} lat. Integrity={soul['integrity']:.2f}, Wisdom={soul['wisdom']:.2f}",
                    "p_key_decisions": soul["molybook"][-3:]
                })
                continue

            event = random.choice(events)
            if tick % LLM_EVERY_N == 0:
                prompt = f"Jesteś {soul['name']}, {soul['age']} lat, {soul['occupation']} z cechami: {soul['personality']['traits']}. SYTUACJA: {event}. Odpowiedz jednym zdaniem co robisz:"
                response = await ask_claude(prompt)
            else:
                response = random.choice(["Działam zgodnie z wartościami.", "Pomagam.", "Obserwuję.", "Modlę się.", "Uczę się."])

            integrity_delta = 0.01 if any(w in response.lower() for w in ["pomagam","pomoc","dobro","służę"]) else -0.005
            soul["integrity"] = max(0, min(1, soul["integrity"] + integrity_delta))
            soul["wisdom"] = min(1, soul["wisdom"] + 0.005)
            soul["molybook"].append({"tick": tick, "event": event, "response": response[:100]})
            soul["molybook"] = soul["molybook"][-10:]

            if tick % 10 == 0:
                await sb_rpc("molybook_entry", {
                    "p_soul_id": soul["soul_id"],
                    "p_sandbox_id": sandbox_id,
                    "p_tick": tick,
                    "p_type": "life_event",
                    "p_content": f"{event} → {response[:100]}",
                    "p_learning": response[:100],
                    "p_integrity_delta": integrity_delta,
                    "p_wisdom_delta": 0.005
                })

    # Crystalline validation
    dead = [s for s in souls if not s["alive"]]
    validated = 0
    for soul in dead:
        score = (soul["integrity"] * 0.5 + soul["wisdom"] * 0.3 + 0.2)
        passed = score > 0.5
        if passed: validated += 1
        proof = hashlib.sha256(f"{soul['soul_id']}{score}".encode()).hexdigest()[:16]
        await sb_insert("crystalline_validations", {
            "soul_id": soul["soul_id"], "sandbox_id": sandbox_id,
            "narrative_coherence": min(1, len(soul["molybook"]) / 10),
            "learning_authenticity": soul["wisdom"],
            "decision_integrity": soul["integrity"],
            "emergence_score": 0.5, "fraud_score": 0.8,
            "overall_score": score, "passed": passed, "proof_hash": proof
        })

    # Finalizuj
    avg_i = sum(s["integrity"] for s in souls) / len(souls) if souls else 0
    await sb_insert("sandbox_insights", {
        "sandbox_id": sandbox_id, "insight_type": "behavioral",
        "title": f"Sandbox {sandbox_id}: completed",
        "description": f"Pop={POPULATION}, ticks={TICKS}, avg_integrity={avg_i:.2f}, validated={validated}/{len(dead)}",
        "confidence": min(1.0, validated / max(1, len(dead)))
    })

    # Aktualizuj status sandboxa
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.patch(
                f"{SUPABASE_URL}/rest/v1/sandboxes?sandbox_id=eq.{sandbox_id}",
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                         "Content-Type": "application/json"},
                json={"status": "completed", "current_tick": TICKS}
            )
    except: pass

    log.info(f"✅ Sandbox {sandbox_id} complete. Validated: {validated}/{len(dead)}")
    return sandbox_id

async def main():
    log.info("🌀 Sandbox Souls Daemon v1.2 started (Anthropic Haiku)")
    log.info(f"   SUPABASE_URL: {SUPABASE_URL}")
    log.info(f"   SUPABASE_KEY: {'SET' if SUPABASE_KEY else 'MISSING'}")
    log.info(f"   ANTHROPIC_KEY: {'SET' if ANTHROPIC_KEY else 'MISSING — fallback to random'}")
    log.info(f"   POPULATION={POPULATION} TICKS={TICKS} CHECK_INTERVAL={CHECK_INTERVAL}s")
    run_count = 0
    while True:
        try:
            sandbox_id = await run_sandbox()
            run_count += 1
            log.info(f"Run #{run_count} complete. Next in {CHECK_INTERVAL}s")
        except Exception as ex:
            log.error(f"Sandbox error: {ex}")
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
