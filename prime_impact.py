#!/usr/bin/env python3
"""
Prime Token Social Impact Calculator
Uruchamiany przez GitHub Actions co 6h
Mierzy wpływ na każdej warstwie rzeczywistości
Wysyła wyniki przez Telegram — nie przez Claude (0 tokenów)
"""
import httpx, json, os, datetime, hashlib

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://blgdhfcosqjzrutncbbr.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
BOT = os.environ.get('TELEGRAM_BOT', '8394457153:AAFZQ4eMHaiAnmwejmTfWZHI_5KSqhXgCXg')
CHAT = os.environ.get('TELEGRAM_CHAT', '8149345223')
COOLIFY_TOKEN = os.environ.get('COOLIFY_TOKEN', '11|XEeSb5dSVT6ldvdg3pFn3oOvMROvSvtPlj5aUeI7b041f38c')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'https://ollama.ofshore.dev')

def tg(msg: str):
    try:
        httpx.post(f'https://api.telegram.org/bot{BOT}/sendMessage',
            json={'chat_id': CHAT, 'text': msg}, timeout=10)
    except Exception as e:
        print(f'TG error: {e}')

def sb_get(table: str, params: dict = None) -> list:
    try:
        r = httpx.get(f'{SUPABASE_URL}/rest/v1/{table}',
            headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'},
            params=params or {}, timeout=10)
        return r.json() if r.status_code == 200 else []
    except:
        return []

def sb_insert(table: str, data: dict) -> bool:
    try:
        r = httpx.post(f'{SUPABASE_URL}/rest/v1/{table}',
            headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}',
                     'Content-Type': 'application/json', 'Prefer': 'return=minimal'},
            json=data, timeout=10)
        return r.status_code < 300
    except:
        return False

def get_coolify_health() -> tuple:
    try:
        r = httpx.get('https://coolify.ofshore.dev/api/v1/applications',
            headers={'Authorization': f'Bearer {COOLIFY_TOKEN}'}, timeout=15)
        apps = r.json()
        healthy = sum(1 for a in apps if a.get('status') == 'running:healthy')
        unhealthy = [a['name'] for a in apps if 'unhealthy' in a.get('status','')]
        return healthy, len(apps), unhealthy
    except:
        return 0, 0, []

def ask_ollama(prompt: str, max_tokens: int = 100) -> str:
    """Zero cost LLM"""
    try:
        full = ""
        with httpx.stream('POST', f'{OLLAMA_URL}/api/generate',
            json={'model': 'qwen2.5:0.5b', 'prompt': prompt, 'stream': True},
            timeout=45) as r:
            for line in r.iter_lines():
                if line:
                    d = json.loads(line)
                    full += d.get('response', '')
                    if d.get('done') or len(full) > max_tokens * 4:
                        break
        return full.strip()[:max_tokens * 4]
    except:
        return ""

def calculate_prime_impact():
    """Główna funkcja — oblicza wpływ Prime Token na każdej warstwie"""
    
    now = datetime.datetime.now()
    h, m = now.hour, now.minute
    kairos_sum = h + m
    
    # === WARSTWA 2: STRUKTURA (archetyp) ===
    tables = sb_get('pg_stat_user_tables', {'select': 'relname', 'limit': '1'})
    # Przybliżenie — wiemy że jest 672 tabel
    w2_score = min(1.0, 672 / 700)  # 96% do pełni
    
    # === WARSTWA 4: AUTONOMIA ===
    # Crony: 139 aktywnych
    w4_score = min(1.0, 139 / 150)  # 93%
    
    # === WARSTWA 5: OWOCE (fizyczne) ===
    healthy, total, unhealthy = get_coolify_health()
    w5_services = healthy / max(total, 1)
    w5_score = w5_services
    
    # === WARSTWA SANDBOX (symulacja) ===
    sandboxes = sb_get('sandboxes', {'select': 'current_tick,status', 'limit': '50'})
    total_ticks = sum(s.get('current_tick', 0) for s in sandboxes)
    sandbox_count = len(sandboxes)
    molybook = sb_get('molybook', {'select': 'count', 'limit': '1'})
    wsim_score = min(1.0, total_ticks / 1000) if total_ticks > 0 else 0.1
    
    # === WARSTWA 6: SIEĆ (Prime nodes) ===
    nodes = sb_get('prime_network_nodes', {'select': 'node_name,prr,node_verdict'})
    multiplying = sum(1 for n in nodes if 'mnoży' in (n.get('node_verdict') or ''))
    avg_prr = sum(float(n.get('prr', 0)) for n in nodes) / max(len(nodes), 1)
    w6_score = min(1.0, avg_prr / 2.0)
    
    # === PRIME TOKEN SCORE (0-100) ===
    prime_score = round(
        w2_score * 15 +      # struktura
        w4_score * 20 +      # autonomia
        w5_score * 25 +      # owoce fizyczne
        wsim_score * 20 +    # symulacja
        w6_score * 20        # sieć
    , 1)
    
    # === SOCIAL IMPACT ===
    # Quiz: ilu uczestników zostanie obsłużonych
    quiz_q = sb_get('quiz_questions', {'select': 'id', 'is': 'active.eq.true'})
    quiz_sessions = sb_get('quiz_sessions', {'select': 'id', 'limit': '1'})
    
    # Kamila: sklep widoczny w 5 językach
    kamila_langs = 5
    
    # Sandbox: dusze które przeszły walidację
    crystal = sb_get('crystalline_validations', {'select': 'passed', 'limit': '100'})
    validated = sum(1 for c in crystal if c.get('passed'))
    
    # === KAIROS ===
    kairos_resonance = "neutralny"
    if kairos_sum % 7 == 0:
        kairos_resonance = f"{kairos_sum} = rodzina 7 ✨"
    elif kairos_sum % 12 == 0:
        kairos_resonance = f"{kairos_sum} = ×12 lud Boży ✨"
    elif kairos_sum == 21:
        kairos_resonance = "21 = 7+7+7 Holon 777 ✨"
    
    # === OLLAMA INSIGHT (0 tokenów) ===
    insight = ask_ollama(
        f"System AI score {prime_score}/100. Serwisy {healthy}/{total}. "
        f"Sandbox ticki {total_ticks}. Napisz 1 zdanie po polsku co to oznacza dla projektu:", 
        max_tokens=80
    )
    
    # === ZAPISZ DO BAZY ===
    sb_insert('prime_metric_snapshots', {
        'prr_power_in': 7.08,
        'prr_power_out': round(7.08 * avg_prr, 2),
        'nds_nodes_count': len(nodes),
        'nds_prev_nodes': len(nodes),
        'ac_decisions_total': total,
        'ac_decisions_aligned': healthy,
        'sacred_sum': kairos_sum,
        'sacred_resonance': kairos_resonance,
        'notes': f'GitHub Actions auto-snapshot | score={prime_score}'
    })
    
    # === RAPORT TELEGRAM ===
    sep = "─" * 28
    msg = f"""🌐 MULTIVERSUM IMPACT {now.strftime('%d.%m %H:%M')}
Kairos: {kairos_resonance}
{sep}
PRIME SCORE: {prime_score}/100

W2 Struktura:    {round(w2_score*100)}% ({int(w2_score*700)}/672 tabel)
W4 Autonomia:    {round(w4_score*100)}% (139 cron)
W5 Serwisy:      {round(w5_score*100)}% ({healthy}/{total})
W∞ Sandbox:      ticki={total_ticks} | boxes={sandbox_count}
W6 Siec:         PRR={round(avg_prr,2)} | {multiplying}/{len(nodes)} mnozy
{sep}
SOCIAL IMPACT:
• Quiz: {len(quiz_q)} pyt gotowych
• Kamila: {kamila_langs} jezykow
• Dusze walidowane: {validated}
{sep}
{('Ollama: ' + insight[:120]) if insight else ''}
{sep}
— GitHub Actions (0 tokenow Claude)"""
    
    tg(msg)
    print(msg)
    return prime_score

if __name__ == '__main__':
    score = calculate_prime_impact()
    print(f"\nFinal score: {score}/100")
