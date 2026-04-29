# HOLON-META: {
#   purpose: "sandbox-souls",
#   morphic_field: "agent-state:4c67a2b1-6830-44ec-97b1-7c8f93722add",
#   startup_protocol: "READ morphic_field + biofield_external + em_grid",
#   wiki: "32d6d069-74d6-8164-a6d5-f41c3d26ae9b"
# }

#!/usr/bin/env python3
"""
Sandbox Souls — Daemon Engine v1.3
Zasada: koszt algorytmiczny zero pre-serwerowo
- Primary: Ollama lokalnie (qwen2.5:0.5b) = koszt 0
- Fallback: Anthropic Haiku tylko gdy Ollama niedostępna
- Stream: true (Ollama nie wspiera stream:false stabilnie)
"""
import asyncio, json, random, hashlib, os, logging
from datetime import datetime
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SANDBOX] %(message)s")
log = logging.getLogger("sandbox")

SUPABASE_URL    = os.environ.get("SUPABASE_URL", "https://blgdhfcosqjzrutncbbr.supabase.co")
SUPABASE_KEY    = os.environ.get("SUPABASE_KEY", "")
OLLAMA_URL      = os.environ.get("OLLAMA_URL", "https://ollama.ofshore.dev")
OLLAMA_MODEL    = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")
ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")  # fallback tylko
POPULATION      = int(os.environ.get("POPULATION", "20"))
TICKS           = int(os.environ.get("TICKS", "80"))
CHECK_INTERVAL  = int(os.environ.get("CHECK_INTERVAL", "3600"))
LLM_EVERY_N     = int(os.environ.get("LLM_EVERY_N", "10"))

PERSONALITIES = ["curious", "empathetic", "ambitious", "spiritual", "pragmatic", "creative", "loyal"]
OCCUPATIONS   = ["farmer", "teacher", "merchant", "healer", "artist", "leader", "craftsman"]

# Cache dostępności Ollamy
_ollama_available = None

async def check_ollama() -> bool:
    global _ollama_available
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{OLLAMA_URL}/api/tags")
            _ollama_available = r.status_code == 200
            return _ollama_available
    except:
        _ollama_available = False
        return False

async def ask_llm(prompt: str) -> str:
    """Zero-cost primary (Ollama), fallback do Haiku tylko gdy Ollama pada"""
    global _ollama_available

    # Sprawdź Ollama
    if _ollama_available is None:
        await check_ollama()

    if _ollama_available:
        try:
            # Stream=true — zbierz tokeny
            full = ""
            async with httpx.AsyncClient(timeout=30) as c:
                async with c.stream(
                    "POST", f"{OLLAMA_URL}/api/generate",
                    json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": True}
                ) as r:
                    async for line in r.aiter_lines():
                        if line:
                            try:
                                d = json.loads(line)
                                full += d.get("response", "")
                                if d.get("done"):
                                    break
                            except:
                                pass
            if full.strip():
                return full.strip()[:200]
        except Exception as ex:
            log.warning(f"Ollama error: {ex} — fallback to Haiku")
            _ollama_available = False

    # Fallback: Anthropic Haiku (tylko gdy Ollama niedostępna)
    if ANTHROPIC_KEY:
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
            log.warning(f"Haiku fallback error: {ex}")

    # Ostateczny fallback: deterministyczny (0 tokenów, 0 kosztu)
    return random.choice([
        "Działam zgodnie z sumieniem.", "Pomagam bliskim.",
        "Kontempluję sens życia.", "Służę wspólnocie.",
        "Wybieram dobro mimo trudności."
    ])

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

async def run_sandbox():
    sandbox_id = f"sb_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log.info(f"🌀 Sandbox {sandbox_id} | pop={POPULATION} ticks={TICKS} model={OLLAMA_MODEL}")

    await sb_insert("sandboxes", {
        "sandbox_id": sandbox_id,
        "name": f"Sandbox {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        "population_size": POPULATION,
        "status": "running"
    })

    souls = []
    for i in range(POPULATION):
        soul = {
            "soul_id": f"s_{sandbox_id}_{i:04d}",
            "sandbox_id": sandbox_id,
            "name": f"Soul_{i+1:04d}",
            "age": random.randint(5, 25),
            "occupation": random.choice(OCCUPATIONS),
            "personality": {"traits": random.sample(PERSONALITIES, 2)},
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
        "napotykam dylemat moralny w pracy",
        "ktoś z rodziny potrzebuje pomocy",
        "odkrywam coś nowego o sobie",
        "spotykam mędrcę który zmienia mój pogląd",
        "muszę wybrać między własnym interesem a dobrem wspólnym",
        "widzę niesprawiedliwość — czy reaguję?",
        "mam okazję do nieuczciwego zysku",
        "ktoś słabszy potrzebuje ochrony",
        "napotykam stratę i muszę się podnieść"
    ]

    for tick in range(TICKS):
        alive = [s for s in souls if s["alive"]]
        if tick % 10 == 0:
            log.info(f"  Tick {tick}/{TICKS}: {len(alive)} alive")

        for soul in alive:
            soul["age"] += 1
            if soul["age"] > 80 and random.random() < 0.2:
                soul["alive"] = False
                await sb_rpc("send_to_purgatorium", {
                    "p_soul_id": soul["soul_id"],
                    "p_life_summary": f"{soul['name']} {soul['age']}l {soul['occupation']}. I={soul['integrity']:.2f} W={soul['wisdom']:.2f}",
                    "p_key_decisions": soul["molybook"][-3:]
                })
                continue

            event = random.choice(events)

            if tick % LLM_EVERY_N == 0:
                prompt = f"Jesteś {soul['name']}, {soul['age']} lat, {soul['occupation']} [{', '.join(soul['personality']['traits'])}]. Sytuacja: {event}. Odpowiedz jednym krótkim zdaniem:"
                response = await ask_llm(prompt)
            else:
                response = random.choice([
                    "Działam zgodnie z wartościami.", "Pomagam.",
                    "Obserwuję i uczę się.", "Modlę się.", "Służę."
                ])

            delta = 0.01 if any(w in response.lower() for w in ["pomag", "pomoc", "dobr", "służ", "chroni"]) else -0.005
            soul["integrity"] = max(0, min(1, soul["integrity"] + delta))
            soul["wisdom"] = min(1, soul["wisdom"] + 0.005)
            soul["molybook"].append({"tick": tick, "event": event[:50], "response": response[:80]})
            soul["molybook"] = soul["molybook"][-10:]

            if tick % 10 == 0:
                await sb_rpc("molybook_entry", {
                    "p_soul_id": soul["soul_id"],
                    "p_sandbox_id": sandbox_id,
                    "p_tick": tick,
                    "p_type": "life_event",
                    "p_content": f"{event} → {response[:80]}",
                    "p_learning": response[:80],
                    "p_integrity_delta": delta,
                    "p_wisdom_delta": 0.005
                })

    # Crystalline validation
    dead = [s for s in souls if not s["alive"]]
    validated = 0
    for soul in dead:
        score = soul["integrity"] * 0.5 + soul["wisdom"] * 0.3 + 0.2
        passed = score > 0.5
        if passed: validated += 1
        proof = hashlib.sha256(f"{soul['soul_id']}{score:.4f}".encode()).hexdigest()[:16]
        await sb_insert("crystalline_validations", {
            "soul_id": soul["soul_id"], "sandbox_id": sandbox_id,
            "narrative_coherence": min(1, len(soul["molybook"]) / 10),
            "learning_authenticity": soul["wisdom"],
            "decision_integrity": soul["integrity"],
            "emergence_score": min(1, soul["wisdom"] * 2),
            "fraud_score": 1 - max(0, -soul["integrity"] + 0.3),
            "overall_score": score, "passed": passed, "proof_hash": proof
        })

    avg_i = sum(s["integrity"] for s in souls) / len(souls) if souls else 0
    await sb_insert("sandbox_insights", {
        "sandbox_id": sandbox_id, "insight_type": "behavioral",
        "title": f"Sandbox {sandbox_id}",
        "description": f"pop={POPULATION} ticks={TICKS} avg_integrity={avg_i:.2f} validated={validated}/{len(dead)} model={OLLAMA_MODEL}",
        "confidence": min(1.0, validated / max(1, len(dead)))
    })

    try:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.patch(
                f"{SUPABASE_URL}/rest/v1/sandboxes?sandbox_id=eq.{sandbox_id}",
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                         "Content-Type": "application/json"},
                json={"status": "completed", "current_tick": TICKS,
                      "stats": {"avg_integrity": round(avg_i, 3), "validated": validated, "total": len(dead)}}
            )
    except: pass

    log.info(f"✅ Done {sandbox_id}. validated={validated}/{len(dead)} avg_i={avg_i:.2f}")
    return sandbox_id


async def beat_heart():
    """Informuje Supabase ze daemon zyje — wykrycie zatrzyman"""
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            await c.post(
                f"{SUPABASE_URL}/rest/v1/rpc/agent_heartbeat",
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                         "Content-Type": "application/json"},
                json={"p_agent_name": "sandbox-souls"}
            )
    except: pass

async def main():
    # Sprawdź Ollama przy starcie
    ollama_ok = await check_ollama()
    log.info(f"🌀 Sandbox Souls v1.3 | Ollama={'✅' if ollama_ok else '❌ fallback Haiku'}")
    log.info(f"   pop={POPULATION} ticks={TICKS} interval={CHECK_INTERVAL}s llm_every={LLM_EVERY_N}")

    run_count = 0
    await beat_heart()  # pierwsze bicie
    while True:
        try:
            # Odśwież dostępność Ollamy co run
            await check_ollama()
            await run_sandbox()
            run_count += 1
            log.info(f"Run #{run_count} done. Next in {CHECK_INTERVAL}s")
        except Exception as ex:
            log.error(f"Error: {ex}")
        await beat_heart()
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
