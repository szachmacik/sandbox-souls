#!/usr/bin/env python3
"""
Purgatorium Service — Dusze wybierają swój los po śmierci
==========================================================
Opcje:
  A. Sleep — zamarznięcie w bazie, spokój
  B. Contemplate — głęboka refleksja, transferuj mądrość
  C. Sainthood — stań się źródłem wiedzy dla innych dusz
  D. Dissolve — całkowita ekstrakcja wzorców i reset
"""
import asyncio, os, json, random, logging
import httpx

log = logging.getLogger("purgatorium")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://blgdhfcosqjzrutncbbr.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

async def sb_query(table, filters=""):
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{SUPABASE_URL}/rest/v1/{table}?{filters}",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"})
        return r.json() if r.status_code == 200 else []

async def sb_update(table, match, data):
    params = "&".join(f"{k}=eq.{v}" for k,v in match.items())
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.patch(f"{SUPABASE_URL}/rest/v1/{table}?{params}",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                     "Content-Type": "application/json"},
            json=data)
        return r.status_code < 300

async def make_choice(soul_record: dict) -> str:
    """Dusza wybiera własny los na podstawie swojego życia."""
    integrity = soul_record.get("final_integrity", 0.5)
    wisdom = soul_record.get("final_wisdom", 0.0)
    
    # Heurystyczny wybór (bez AI = €0 koszt)
    if wisdom > 0.7:
        choice = "sainthood"   # Mądrzy stają się mentorami
    elif integrity > 0.8:
        choice = "contemplate" # Prawi kontemplują i transferują mądrość
    elif integrity > 0.5:
        choice = "sleep"       # Przeciętni śpią
    else:
        choice = "dissolve"    # Słabe dusze są resety do ekstrakcji wzorców
    
    return choice

async def process_purgatorium():
    """Przetwarzaj dusze czekające w Purgatorium."""
    waiting = await sb_query("purgatorium", "status=eq.waiting&limit=10")
    log.info(f"Purgatorium: {len(waiting)} souls waiting")
    
    for soul in waiting:
        choice = await make_choice(soul)
        wisdom_transferred = soul.get("final_wisdom", 0) * 0.7 if choice in ["contemplate", "sainthood"] else 0
        
        await sb_update("purgatorium", {"soul_id": soul["soul_id"]}, {
            "choice": choice,
            "choice_reason": f"Based on integrity={soul.get('final_integrity',0):.2f}, wisdom={soul.get('final_wisdom',0):.2f}",
            "wisdom_transferred": wisdom_transferred,
            "status": "chosen"
        })
        log.info(f"  ✦ {soul['soul_id'][:20]} → {choice} (wisdom_transfer={wisdom_transferred:.2f})")
    
    return len(waiting)

async def main():
    log.basicConfig(level=logging.INFO, format="%(asctime)s [PURGA] %(message)s")
    interval = int(os.environ.get("CHECK_INTERVAL", "60"))
    log.info("☯ Purgatorium Service started")
    
    while True:
        try:
            processed = await process_purgatorium()
            if processed:
                log.info(f"Processed {processed} souls")
        except Exception as ex:
            log.error(f"Error: {ex}")
        await asyncio.sleep(interval)

if __name__ == "__main__":
    asyncio.run(main())
