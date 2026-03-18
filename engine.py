#!/usr/bin/env python3
"""
Sandbox People Ecosystem — Simulation Engine v1
================================================
HOLON Philosophy: każda dusza = całość I część
- Całość: pełna historia, osobowość, relacje, wolna wola
- Część: należy do rodziny → sandboxa → Purgatorium → wiedzy

Koszt: ~€0 runtime (Ollama lokalnie)
       ~€6 development (Claude API)
"""
import asyncio
import json
import random
import hashlib
import os
import logging
from typing import Optional
from datetime import datetime
import httpx

log = logging.getLogger("sandbox")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [SANDBOX] %(message)s")

# ── Config ────────────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://blgdhfcosqjzrutncbbr.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
OLLAMA_URL   = os.environ.get("OLLAMA_URL", "http://ollama.ofshore.dev")  # lokalny LLM
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")  # mały model, €0
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")  # tylko do walidacji crystalline

# ── Osobowości ────────────────────────────────────────────────────────────────
PERSONALITY_TRAITS = [
    "curious", "cautious", "empathetic", "ambitious", "spiritual",
    "pragmatic", "creative", "loyal", "rebellious", "contemplative"
]
OCCUPATIONS = [
    "farmer", "teacher", "merchant", "healer", "artist",
    "leader", "craftsman", "philosopher", "warrior", "keeper"
]

# ── Supabase helper ───────────────────────────────────────────────────────────
async def sb(func: str, params: dict):
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                f"{SUPABASE_URL}/rest/v1/rpc/{func}",
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                         "Content-Type": "application/json"},
                json=params
            )
            return r.json()
    except Exception as ex:
        log.warning(f"Supabase {func}: {ex}")
        return {}

async def sb_insert(table: str, data: dict):
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                f"{SUPABASE_URL}/rest/v1/{table}",
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                         "Content-Type": "application/json", "Prefer": "return=minimal"},
                json=data
            )
            return r.status_code < 300
    except Exception as ex:
        log.warning(f"Insert {table}: {ex}")
        return False

async def sb_update(table: str, match: dict, data: dict):
    try:
        params = "&".join(f"{k}=eq.{v}" for k,v in match.items())
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.patch(
                f"{SUPABASE_URL}/rest/v1/{table}?{params}",
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                         "Content-Type": "application/json"},
                json=data
            )
            return r.status_code < 300
    except Exception as ex:
        log.warning(f"Update {table}: {ex}")
        return False

# ── Ollama — "29 bytów" — lokalny LLM ────────────────────────────────────────
async def ask_soul_llm(soul: dict, situation: str) -> str:
    """Zapytaj lokalny LLM jak dusza reaguje na sytuację. Koszt: €0."""
    prompt = f"""Jesteś {soul['name']}, {soul['age']}-letnim/letnią {soul.get('occupation','person')}.
Twoje cechy: {', '.join(soul.get('personality',{}).get('traits',[]))}.
Twoja historia (molybook): {soul.get('last_memory','brak')}

SYTUACJA: {situation}

Odpowiedz jednym krótkim zdaniem jak reagujesz i co robisz (max 50 słów, po polsku):"""
    
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False})
            if r.status_code == 200:
                return r.json().get("response", "Milczę i obserwuję.")
    except:
        pass
    # Fallback bez LLM (reguły heurystyczne)
    return random.choice([
        "Działam zgodnie z moimi wartościami.",
        "Pomagam rodzinie w potrzebie.",
        "Zastanawiam się głęboko nad tym wyborem.",
        "Reaguję instynktownie i z sercem."
    ])

# ── Soul — dusza ──────────────────────────────────────────────────────────────
class Soul:
    def __init__(self, soul_id: str, sandbox_id: str, name: str, 
                 personality: dict, family_id: Optional[str] = None):
        self.soul_id = soul_id
        self.sandbox_id = sandbox_id
        self.name = name
        self.age = random.randint(0, 30)  # startowy wiek
        self.personality = personality
        self.family_id = family_id
        self.occupation = random.choice(OCCUPATIONS)
        self.partner_id: Optional[str] = None
        self.children_ids: list = []
        self.friend_ids: list = []
        self.integrity = random.uniform(0.3, 0.9)
        self.wisdom = 0.0
        self.happiness = random.uniform(0.4, 0.8)
        self.molybook: list = []  # lokalna pamięć (ostatnie 20)
        self.last_memory = ""
        self.alive = True
        self.tick = 0

    async def live_tick(self, tick: int, world_events: list, neighbors: list):
        """Jeden tick życia = 1 rok symulacji."""
        self.tick = tick
        self.age += 1
        
        # Naturalna śmierć (po 80+ latach)
        if self.age > 80 and random.random() < 0.15:
            await self.die(tick)
            return
        
        # Zdarzenie życiowe
        event = self._pick_event(world_events)
        
        # Reakcja duszy przez LLM
        situation = f"{event} (wiek: {self.age}, rodzina: {'tak' if self.family_id else 'nie'})"
        response = await ask_soul_llm(self.__dict__, situation)
        
        # Wylicz wpływ na integrity i wisdom
        integrity_delta = self._eval_integrity(event, response)
        wisdom_delta = 0.01 if self.age > 20 else 0.005
        
        # Zapis do molybook (lokalnie + Supabase)
        entry = {
            "tick": tick, "type": "life_event",
            "content": f"{event} → {response}",
            "integrity_delta": integrity_delta,
            "wisdom_delta": wisdom_delta
        }
        self.molybook.append(entry)
        if len(self.molybook) > 20:
            self.molybook = self.molybook[-20:]
        self.last_memory = entry["content"]
        
        # Aktualizuj wskaźniki
        self.integrity = max(0, min(1, self.integrity + integrity_delta))
        self.wisdom = max(0, min(1, self.wisdom + wisdom_delta))
        
        # Zapisz do Supabase (co 10 ticków żeby nie przeciążać)
        if tick % 10 == 0:
            await sb("molybook_entry", {
                "p_soul_id": self.soul_id,
                "p_sandbox_id": self.sandbox_id,
                "p_tick": tick,
                "p_type": "life_event",
                "p_content": entry["content"],
                "p_learning": self._extract_learning(response),
                "p_integrity_delta": integrity_delta,
                "p_wisdom_delta": wisdom_delta
            })
        
        # Interakcja z sąsiadami (emergencja przez relacje)
        if neighbors and random.random() < 0.3:
            neighbor = random.choice(neighbors)
            if random.random() < 0.1:  # szansa na przyjaźń
                if neighbor.soul_id not in self.friend_ids:
                    self.friend_ids.append(neighbor.soul_id)

    def _pick_event(self, world_events: list) -> str:
        personal = [
            "muszę zdecydować czy pomóc obcej osobie",
            "spotykam kogoś kto potrzebuje rady",
            "napotykam dylemat moralny w pracy",
            "mam szansę zdobyć bogactwo kosztem innych",
            "ktoś z rodziny potrzebuje pomocy",
            "odkrywam coś co zmienia mój sposób myślenia",
            "muszę wybrać między lojalnością a prawdą"
        ]
        events = personal + (world_events or [])
        return random.choice(events)

    def _eval_integrity(self, event: str, response: str) -> float:
        """Ocen wpływ decyzji na integralność duszy."""
        positive = ["pomagam", "dbam", "chronię", "uczę", "dzielę", "wspieram"]
        negative = ["unikam", "kłamię", "kradnę", "oszukuję", "porzucam"]
        
        response_lower = response.lower()
        score = 0.0
        for w in positive:
            if w in response_lower:
                score += 0.02
        for w in negative:
            if w in response_lower:
                score -= 0.03
        return score

    def _extract_learning(self, response: str) -> str:
        return f"W wieku {self.age}: {response[:100]}"

    async def die(self, tick: int):
        """Dusza umiera → idzie do Purgatorium."""
        self.alive = False
        log.info(f"  ☽ {self.name} umiera (wiek {self.age}, integrity={self.integrity:.2f}, wisdom={self.wisdom:.2f})")
        
        # Podsumowanie życia
        summary = (
            f"{self.name} żył/a {self.age} lat jako {self.occupation}. "
            f"Integrity: {self.integrity:.2f}, Wisdom: {self.wisdom:.2f}. "
            f"Rodzina: {'tak' if self.family_id else 'nie'}. "
            f"Przyjaciół: {len(self.friend_ids)}. "
            f"Ostatnia pamięć: {self.last_memory[:200]}"
        )
        
        key_decisions = self.molybook[-5:] if self.molybook else []
        
        await sb("send_to_purgatorium", {
            "p_soul_id": self.soul_id,
            "p_life_summary": summary,
            "p_key_decisions": key_decisions
        })
        
        await sb_update("souls", {"soul_id": self.soul_id}, {"status": "purgatorium", "died_at_tick": tick})

# ── Crystalline Validator ─────────────────────────────────────────────────────
class CrystallineValidator:
    """Ocena duszy przed uploadem mądrości do systemu."""
    
    async def validate(self, soul: Soul) -> dict:
        checks = {
            "narrative_coherence": self._check_narrative(soul),
            "learning_authenticity": self._check_learning(soul),
            "decision_integrity": soul.integrity,
            "emergence_score": self._check_emergence(soul),
            "fraud_score": 1.0 - self._check_fraud(soul),
        }
        overall = sum(checks.values()) / len(checks)
        passed = overall > 0.6
        
        # Crystalline hash
        proof = hashlib.sha256(
            f"{soul.soul_id}{soul.integrity}{soul.wisdom}{overall}".encode()
        ).hexdigest()[:16]
        
        result = {
            **checks,
            "overall_score": overall,
            "passed": passed,
            "proof_hash": proof
        }
        
        # Zapisz do Supabase
        await sb_insert("crystalline_validations", {
            "soul_id": soul.soul_id,
            "sandbox_id": soul.sandbox_id,
            **checks,
            "overall_score": overall,
            "passed": passed,
            "proof_hash": proof
        })
        
        if passed:
            await sb_update("souls", {"soul_id": soul.soul_id}, {
                "crystalline_score": overall,
                "crystalline_proof": proof,
                "validation_passed": True
            })
        
        return result

    def _check_narrative(self, soul: Soul) -> float:
        """Czy dusza ma spójną historię?"""
        if len(soul.molybook) < 3:
            return 0.5
        return min(1.0, len(soul.molybook) / 20) * 0.8 + 0.2

    def _check_learning(self, soul: Soul) -> float:
        """Czy dusza się uczyła (wzrost wisdom)?"""
        return min(1.0, soul.wisdom * 5)

    def _check_emergence(self, soul: Soul) -> float:
        """Czy pojawiły się nieoczekiwane wzorce?"""
        has_family = 1 if soul.family_id else 0
        has_friends = min(1.0, len(soul.friend_ids) / 5)
        return (has_family * 0.4 + has_friends * 0.6)

    def _check_fraud(self, soul: Soul) -> float:
        """Czy dusza manipulowała? (niski fraud = dobra dusza)"""
        fraud_signals = sum(1 for e in soul.molybook 
                           if e.get("integrity_delta", 0) < -0.05)
        return min(1.0, fraud_signals / max(1, len(soul.molybook)))

# ── Sandbox — kontener symulacji ──────────────────────────────────────────────
class Sandbox:
    def __init__(self, sandbox_id: str, population: int = 100):
        self.sandbox_id = sandbox_id
        self.population = population
        self.souls: list[Soul] = []
        self.tick = 0
        self.validator = CrystallineValidator()
        self.world_events = [
            "wybucha epidemia w regionie",
            "nadchodzi okres dobrobytu",
            "lokalna społeczność organizuje święto",
            "pojawia się obcy wędrowiec z wiedzą",
            "zbiory są wyjątkowo dobre w tym roku",
            "konflikt między dwiema grupami eskaluje"
        ]

    async def spawn_population(self):
        """Stwórz populację z rodzinami."""
        log.info(f"Spawning {self.population} souls in sandbox {self.sandbox_id}...")
        
        # Stwórz sandbox w Supabase
        await sb_insert("sandboxes", {
            "sandbox_id": self.sandbox_id,
            "population_size": self.population,
            "status": "running"
        })
        
        # Stwórz rodziny (co 4 osoby = 1 rodzina)
        family_count = self.population // 4
        for fi in range(family_count):
            family_id = f"family_{self.sandbox_id}_{fi}"
            await sb_insert("soul_families", {
                "family_id": family_id,
                "sandbox_id": self.sandbox_id,
                "family_values": {"cohesion": random.uniform(0.4, 0.9)}
            })
        
        for i in range(self.population):
            name = f"Soul_{i+1:04d}"
            traits = random.sample(PERSONALITY_TRAITS, 3)
            personality = {"traits": traits, "openness": random.uniform(0.3, 0.9)}
            family_id = f"family_{self.sandbox_id}_{i // 4}"
            
            soul_id = await sb("spawn_soul", {
                "p_sandbox_id": self.sandbox_id,
                "p_name": name,
                "p_personality": personality,
                "p_family_id": family_id
            })
            
            if not soul_id:
                soul_id = f"soul_{self.sandbox_id}_{i}"
            
            soul = Soul(soul_id, self.sandbox_id, name, personality, family_id)
            self.souls.append(soul)
        
        log.info(f"✅ {len(self.souls)} souls spawned")

    async def run(self, ticks: int = 80):
        """Uruchom symulację na N ticków (= lat)."""
        await self.spawn_population()
        
        for tick in range(ticks):
            self.tick = tick
            alive_souls = [s for s in self.souls if s.alive]
            
            if tick % 10 == 0:
                log.info(f"  Tick {tick}: {len(alive_souls)} souls alive")
            
            # World event (co 20 ticków)
            world_event = random.choice(self.world_events) if tick % 20 == 0 else ""
            
            # Każda dusza żyje swój tick
            tasks = []
            for soul in alive_souls:
                neighbors = random.sample(alive_souls, min(5, len(alive_souls)))
                tasks.append(soul.live_tick(tick, [world_event] if world_event else [], neighbors))
            
            # Równolegle (batch po 20 żeby nie przeciążać)
            for i in range(0, len(tasks), 20):
                await asyncio.gather(*tasks[i:i+20])
        
        log.info(f"Simulation complete. Validating souls...")
        await self.validate_and_extract()

    async def validate_and_extract(self):
        """Walidacja wszystkich dusz → ekstrakacja wiedzy."""
        dead_souls = [s for s in self.souls if not s.alive]
        validated = 0
        insights = []
        
        for soul in dead_souls[:20]:  # waliduj pierwsze 20 (demo)
            result = await self.validator.validate(soul)
            if result["passed"]:
                validated += 1
        
        log.info(f"✅ Validated: {validated}/{len(dead_souls)} souls passed crystalline check")
        
        # Generuj insight z sandboxa
        if validated > 0:
            avg_integrity = sum(s.integrity for s in self.souls) / len(self.souls)
            insight = {
                "sandbox_id": self.sandbox_id,
                "insight_type": "behavioral",
                "title": f"Sandbox {self.sandbox_id}: integrity patterns",
                "description": f"Average integrity: {avg_integrity:.2f}. Validated souls: {validated}.",
                "confidence": min(1.0, validated / 10)
            }
            await sb_insert("sandbox_insights", insight)
        
        # Aktualizuj status sandboxa
        await sb_update("sandboxes", {"sandbox_id": self.sandbox_id}, {
            "status": "completed",
            "stats": {
                "total_souls": len(self.souls),
                "validated": validated,
                "avg_integrity": sum(s.integrity for s in self.souls) / len(self.souls)
            }
        })

# ── Entry point ───────────────────────────────────────────────────────────────
async def main():
    sandbox_id = f"sandbox_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    population = int(os.environ.get("POPULATION", "50"))  # 50 na start
    ticks = int(os.environ.get("TICKS", "30"))            # 30 lat na start
    
    log.info(f"🌀 SANDBOX PEOPLE ECOSYSTEM — Starting {sandbox_id}")
    log.info(f"   Population: {population} | Ticks: {ticks}")
    
    sandbox = Sandbox(sandbox_id, population)
    await sandbox.run(ticks)
    
    log.info("✅ Sandbox complete. Souls in Purgatorium await their choice.")

if __name__ == "__main__":
    asyncio.run(main())
