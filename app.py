import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import json, math, re, time, random
from datetime import datetime

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

st.set_page_config(
    page_title="Axon · AI Command Center",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)


DEFAULT_API_KEYS = list(st.secrets.get("api_keys", {}).values())


BUILDER = {
    "initials": "S",
    "name":     "Ashwanth Sankar",
    "role":     "𝑰 𝒂𝒎 𝑨𝒔𝒉𝒘𝒂𝒏𝒕𝒉 𝑺𝒂𝒏𝒌𝒂𝒓, 𝒔𝒕𝒖𝒅𝒚𝒊𝒏𝒈 7𝒕𝒉 𝒔𝒕𝒂𝒏𝒅𝒂𝒓𝒅. 𝑰’𝒎 𝒂 𝒑𝒂𝒔𝒔𝒊𝒐𝒏𝒂𝒕𝒆 𝒃𝒖𝒊𝒍𝒅𝒆𝒓 𝒂𝒏𝒅 𝒑𝒓𝒐𝒃𝒍𝒆𝒎-𝒔𝒐𝒍𝒗𝒆𝒓 𝒘𝒊𝒕𝒉 𝒂 𝒔𝒕𝒓𝒐𝒏𝒈 𝒊𝒏𝒕𝒆𝒓𝒆𝒔𝒕 𝒊𝒏 𝑨𝒓𝒕𝒊𝒇𝒊𝒄𝒊𝒂𝒍 𝑰𝒏𝒕𝒆𝒍𝒍𝒊𝒈𝒆𝒏𝒄𝒆 𝒂𝒏𝒅 𝑺𝒆𝒄𝒖𝒓𝒊𝒕𝒚. 𝑰 𝒆𝒏𝒋𝒐𝒚 𝒄𝒓𝒆𝒂𝒕𝒊𝒏𝒈 𝒑𝒓𝒂𝒄𝒕𝒊𝒄𝒂𝒍 𝒔𝒐𝒍𝒖𝒕𝒊𝒐𝒏𝒔, 𝒍𝒆𝒂𝒓𝒏𝒊𝒏𝒈 𝒏𝒆𝒘 𝒕𝒆𝒄𝒉𝒏𝒐𝒍𝒐𝒈𝒊𝒆𝒔 𝒒𝒖𝒊𝒄𝒌𝒍𝒚, 𝒂𝒏𝒅 𝒘𝒐𝒓𝒌𝒊𝒏𝒈 𝒘𝒊𝒕𝒉 𝒕𝒆𝒂𝒎𝒔 𝒕𝒐 𝒕𝒖𝒓𝒏 𝒊𝒅𝒆𝒂𝒔 𝒊𝒏𝒕𝒐 𝒊𝒎𝒑𝒂𝒄𝒕𝒇𝒖𝒍 𝒑𝒓𝒐𝒋𝒆𝒄𝒕𝒔. 𝑨𝒍𝒘𝒂𝒚𝒔 𝒓𝒆𝒂𝒅𝒚 𝒕𝒐 𝒊𝒏𝒏𝒐𝒗𝒂𝒕𝒆, 𝒄𝒐𝒍𝒍𝒂𝒃𝒐𝒓𝒂𝒕𝒆, 𝒂𝒏𝒅 𝒕𝒂𝒌𝒆 𝒐𝒏 𝒏𝒆𝒘 𝒄𝒉𝒂𝒍𝒍𝒆𝒏𝒈𝒆𝒔. 🚀",
    "email":    "ashwanthsankar2k@gmail.com",
    "portfolio": "https://ashwanth.online/",
    "location": "Tamilnadu, India",
    "bio":      "   I am a passionate Python developer and hardware enthusiast. With a strong interest in defense and drone technologies. Looking for hackathons in singapore",
    "skills":   ["DWSA", "AI", "Machine Learning", "Hardware enthusiast", "Drone technologies", "Programming in Python, HTML, CSS"],
}


def classify_error(e):
    msg = str(e).lower()
    if "api_key_invalid" in msg or "api key not valid" in msg or "unauthenticated" in msg: return "AX-401"
    if "permission_denied" in msg or "403" in msg: return "AX-403"
    if "resource_exhausted" in msg or "quota" in msg or "429" in msg or "rate limit" in msg: return "AX-429"
    if "not_found" in msg or "404" in msg: return "AX-404"
    if "internal" in msg or "500" in msg: return "AX-500"
    if "unavailable" in msg or "503" in msg or "overloaded" in msg: return "AX-503"
    return "AX-000"

RETRYABLE_CODES = {"AX-429", "AX-500", "AX-503"}

def gemini_call_with_fallback(keys, call_fn):
    last_err = None
    for key in keys:
        try:
            return call_fn(key)
        except Exception as e:
            code = classify_error(e)
            last_err = (key, code, str(e))
            if code in RETRYABLE_CODES or code in {"AX-401", "AX-403", "AX-404"}:
                continue
            raise
    k, code, msg = last_err
    raise RuntimeError(f"[{code}] All {len(keys)} API keys exhausted. Last: {msg}")

def gemini_json(keys, prompt, system):
    def call(key):
        genai.configure(api_key=key)
        m = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system,
            generation_config={"temperature": 0.2, "response_mime_type": "application/json"})
        return m.generate_content(prompt).text.strip()
    return gemini_call_with_fallback(keys, call)

def gemini_text(keys, prompt, system):
    def call(key):
        genai.configure(api_key=key)
        m = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system,
            generation_config={"temperature": 0.7})
        return m.generate_content(prompt).text.strip()
    return gemini_call_with_fallback(keys, call)



st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&family=Noto+Sans+JP:wght@300;400;700&display=swap');

:root {
  --midnight: #03010a;
  --violet: #7c3aed;
  --violet-light: #a78bfa;
  --sakura: #f9a8d4;
  --blue: #3b82f6;
  --blue-glow: #7dd3fc;
  --green: #34d399;
  --amber: #fbbf24;
  --border: #1e1a30;
}
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background: var(--midnight);
    color: #e2e8f0;
}
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] {
    background: transparent !important;
    height: 2.8rem !important;
}
header[data-testid="stHeader"] > div { background: transparent !important; }
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
}
[data-testid="collapsedControl"] svg { color: #c084fc !important; }
.block-container { padding: 1.2rem 2rem 4rem; max-width: 1200px; margin: auto; }

[data-testid="stSidebar"] {
    background: #05020f !important;
    border-right: 1px solid rgba(168,85,247,0.12) !important;
}
[data-testid="stSidebar"] * { color: #c4b5fd; }

.sidebar-logo {
    font-size: 1.6rem; font-weight: 900;
    background: linear-gradient(135deg, #c084fc, #f0abfc, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: -0.03em; margin-bottom: 0.1rem;
}
.sidebar-sub {
    font-family: 'JetBrains Mono', monospace; font-size: 0.55rem;
    color: #3b2a5a; letter-spacing: 0.14em; text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.sidebar-jp {
    font-family: 'Noto Sans JP', sans-serif; font-size: 0.6rem;
    color: rgba(249,168,212,0.3); letter-spacing: 0.25em; margin-bottom: 1.2rem;
}
.nav-item {
    display: flex; align-items: center; gap: 0.7rem;
    padding: 0.6rem 0.9rem; border-radius: 10px; cursor: pointer;
    margin-bottom: 0.25rem; transition: background 0.2s;
    font-size: 0.85rem; font-weight: 600;
    border: 1px solid transparent;
}
.nav-item.active { background: rgba(124,58,237,0.18); border-color: rgba(168,85,247,0.3); color: #e9d5ff !important; }
.nav-item:hover { background: rgba(168,85,247,0.08); }

/* Background grid */
.jp-grid-bg {
    position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background-image:
        linear-gradient(rgba(168,85,247,0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(168,85,247,0.02) 1px, transparent 1px);
    background-size: 60px 60px;
}
#sakura-canvas {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    pointer-events: none; z-index: 0; opacity: 0.22;
}

/* Right cherry tree — from ron.py original */
#cherry-tree-deco {
    position: fixed; top: 0; right: -60px; height: 100vh; width: 320px;
    pointer-events: none; z-index: 1; opacity: 0.45;
}
#cherry-petal-canvas {
    position: fixed; top: 0; right: 0; width: 340px; height: 100vh;
    pointer-events: none; z-index: 1;
}

/* Monastery deco */
.monastery-deco {
    position: fixed; right: 14px; top: 18%; z-index: 2;
    display: flex; flex-direction: column; gap: 1.4rem;
    opacity: 0.4; pointer-events: none;
}
.monastery-deco svg { filter: drop-shadow(0 0 6px rgba(168,85,247,0.25)); }

/* Status dot */
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: #22c55e;
    box-shadow: 0 0 6px #22c55e; display: inline-block; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }

/* Panels */
.h-panel {
    background: rgba(5,2,15,0.85); border: 1px solid rgba(168,85,247,0.15);
    border-radius: 16px; backdrop-filter: blur(20px); padding: 1.4rem;
}

/* Pipeline cards */
.pipe-card {
    background: #0d0a1f; border: 1px solid #1e1a30;
    border-radius: 12px; padding: 0.9rem 1.3rem;
    margin-bottom: 0.5rem; position: relative; overflow: hidden;
}
.pipe-card::before { content:''; position:absolute; left:0; top:0; bottom:0; width:3px; border-radius:3px 0 0 3px; }
.pipe-card.active { border-color: rgba(125,211,252,0.3); }
.pipe-card.active::before  { background: #7dd3fc; box-shadow: 0 0 14px #7dd3fc88; }
.pipe-card.done::before    { background: #34d399; }
.pipe-card.pending::before { background: #2d2a40; }
.pipe-card.error::before   { background: #f87171; }
.pipe-label { font-family:'JetBrains Mono',monospace; font-size:0.58rem; font-weight:700;
    letter-spacing:0.1em; text-transform:uppercase; color:#475569; margin-bottom:0.1rem; }
.pipe-title { font-size:0.88rem; font-weight:700; color:#e2e8f0; }
.pipe-body  { font-size:0.75rem; color:#64748b; line-height:1.5; margin-top:0.1rem; }

/* Agent cards */
.agent-card {
    background: #0a0520; border: 1px solid rgba(124,58,237,0.3);
    border-radius: 12px; padding: 1rem 1.3rem; margin-bottom: 0.7rem;
    position: relative; overflow: hidden;
}
.agent-card::before {
    content:''; position:absolute; left:0; top:0; bottom:0; width:3px;
    background: linear-gradient(180deg,#c084fc,#a78bfa); border-radius:3px 0 0 3px;
}
.agent-badge {
    font-family:'JetBrains Mono',monospace; font-size:0.58rem; font-weight:700;
    padding:0.15rem 0.5rem; border-radius:99px;
    background: rgba(124,58,237,0.2); color:#c084fc; letter-spacing:0.08em; text-transform:uppercase;
}
.agent-output {
    font-size:0.78rem; color:#c4b5fd; line-height:1.7; white-space:pre-wrap;
    background: rgba(0,0,0,0.3); border-radius:8px; padding:0.7rem 1rem;
    border:1px solid rgba(168,85,247,0.1); margin-top:0.5rem;
    max-height:240px; overflow-y:auto;
}

/* Brain card */
.brain-card {
    background: rgba(10,5,30,0.9); border: 1px solid rgba(124,58,237,0.2);
    border-radius: 14px; padding: 1rem 1.3rem; margin: 0.7rem 0;
}
.brain-title {
    font-family:'JetBrains Mono',monospace; font-size:0.62rem;
    font-weight:700; color:#a78bfa; letter-spacing:0.15em;
    text-transform:uppercase; margin-bottom:0.5rem;
}
.brain-entry {
    font-size:0.76rem; color:#94a3b8; padding:0.35rem 0;
    border-bottom:1px solid rgba(168,85,247,0.08); line-height:1.6;
}
.brain-entry:last-child { border-bottom:none; }

/* QC card */
.qc-card {
    background: rgba(6,3,20,0.9); border: 1px solid rgba(124,58,237,0.2);
    border-radius:12px; padding:0.9rem 1.3rem; margin-bottom:0.9rem;
}
.qc-title { font-family:'JetBrains Mono',monospace; font-size:0.6rem;
    color:#c084fc; letter-spacing:0.12em; text-transform:uppercase; font-weight:700; margin-bottom:0.3rem; }
.qc-row { font-family:'JetBrains Mono',monospace; font-size:0.73rem; color:#a78bfa; margin:0.14rem 0; }

/* Metric grid */
.metric-grid { display:flex; gap:0.7rem; margin:1rem 0; flex-wrap:wrap; }
.metric-box { flex:1; min-width:88px; background:rgba(10,5,30,0.8);
    border:1px solid rgba(168,85,247,0.15); border-radius:10px; padding:0.7rem; text-align:center; }
.metric-val { font-family:'JetBrains Mono',monospace; font-size:1.3rem; font-weight:700;
    background:linear-gradient(135deg,#c084fc,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.metric-lbl { font-size:0.58rem; color:#475569; text-transform:uppercase; letter-spacing:0.08em; margin-top:0.1rem; }

/* Critic / Verifier */
.critic-card   { background:#150a0a; border:1px solid #3a1515; border-radius:12px; padding:0.9rem 1.3rem; margin-bottom:0.7rem; }
.critic-title  { font-family:'JetBrains Mono',monospace; font-size:0.6rem; color:#f87171;
    letter-spacing:0.12em; text-transform:uppercase; font-weight:700; margin-bottom:0.3rem; }
.verifier-card  { background:#0a150a; border:1px solid #153a15; border-radius:12px; padding:0.9rem 1.3rem; margin-bottom:0.7rem; }
.verifier-title { font-family:'JetBrains Mono',monospace; font-size:0.6rem; color:#34d399;
    letter-spacing:0.12em; text-transform:uppercase; font-weight:700; margin-bottom:0.3rem; }

/* Confidence */
.confidence-wrap { background:rgba(10,5,30,0.8); border:1px solid rgba(168,85,247,0.15);
    border-radius:12px; padding:0.9rem 1.2rem; margin:0.7rem 0; }
.confidence-bar-bg { background:rgba(255,255,255,0.06); border-radius:99px; height:8px; overflow:hidden; margin:0.35rem 0; }
.confidence-bar-fill { height:100%; border-radius:99px;
    background:linear-gradient(90deg,#7c3aed,#a78bfa,#f9a8d4); transition:width 1s ease; }

.sec-head {
    font-family:'JetBrains Mono',monospace; font-size:0.58rem;
    letter-spacing:0.14em; text-transform:uppercase; color:#475569;
    margin:1.4rem 0 0.6rem; border-bottom:1px solid rgba(168,85,247,0.1); padding-bottom:0.25rem;
}
.chip-wrap { display:flex; flex-wrap:wrap; gap:0.4rem; margin:0.5rem 0; }
.chip { background:rgba(10,5,30,0.8); border:1px solid rgba(168,85,247,0.2);
    border-radius:99px; padding:0.16rem 0.55rem; font-size:0.66rem;
    color:#94a3b8; font-family:'JetBrains Mono',monospace; }
.chip.done { border-color:#34d399; color:#34d399; }

/* Chat bubbles */
.chat-bubble-user {
    background:linear-gradient(135deg,#1a0f2e,#160e28);
    border:1px solid rgba(124,58,237,0.3); border-radius:18px 18px 4px 18px;
    padding:0.85rem 1.1rem; margin:0.5rem 0 0.5rem auto;
    max-width:80%; font-size:0.88rem; color:#e2e8f0; line-height:1.65; width:fit-content;
}
.chat-bubble-axon {
    background:rgba(5,2,15,0.9); border:1px solid rgba(168,85,247,0.2);
    border-radius:18px 18px 18px 4px;
    padding:0.85rem 1.1rem; margin:0.5rem auto 0.5rem 0;
    max-width:88%; font-size:0.88rem; color:#c4b5fd; line-height:1.7;
    position:relative; overflow:hidden;
}
.chat-bubble-axon::before {
    content:''; position:absolute; left:0; top:0; bottom:0; width:3px;
    background:linear-gradient(180deg,#c084fc,#a78bfa); border-radius:3px 0 0 3px;
}
.axon-avatar { font-size:0.63rem; font-family:'JetBrains Mono',monospace;
    color:#c084fc; letter-spacing:0.1em; margin-bottom:0.25rem; font-weight:700; }
.processing-card {
    background:linear-gradient(135deg,#0a0520,#0d0a1f);
    border:1px solid rgba(168,85,247,0.25); border-radius:14px; padding:1.1rem 1.3rem; margin:0.5rem 0;
}
.processing-title { font-size:0.92rem; font-weight:700; color:#c084fc; margin-bottom:0.35rem; }
.processing-sub { font-size:0.76rem; color:#64748b; line-height:1.6; }

/* Builder card (locked / read-only) */
.builder-card {
    background:rgba(5,2,15,0.9); border:1px solid rgba(168,85,247,0.2);
    border-radius:16px; padding:1.6rem;
}
.builder-avatar {
    width:84px; height:84px; border-radius:50%; flex-shrink:0;
    background:linear-gradient(135deg,#7c3aed,#db2777);
    display:flex; align-items:center; justify-content:center;
    font-weight:900; font-size:2rem; color:white;
    box-shadow:0 0 24px rgba(124,58,237,0.4);
}
.builder-name { font-size:1.4rem; font-weight:800; color:#e9d5ff; letter-spacing:-0.02em; }
.builder-role { font-size:0.78rem; color:#a78bfa; margin-top:0.15rem; font-family:'JetBrains Mono',monospace; }
.builder-field-label { font-size:0.6rem; color:rgba(196,166,255,0.4);
    letter-spacing:0.1em; text-transform:uppercase; margin-bottom:0.2rem; }
.builder-field-val { font-size:0.82rem; color:#c4b5fd; font-family:'JetBrains Mono',monospace; }
.skill-chip { display:inline-block; background:rgba(124,58,237,0.15);
    border:1px solid rgba(168,85,247,0.25); border-radius:99px;
    padding:0.2rem 0.65rem; font-size:0.68rem; color:#c084fc;
    font-family:'JetBrains Mono',monospace; margin:0.2rem; }
.locked-badge { background:rgba(251,191,36,0.12); border:1px solid rgba(251,191,36,0.25);
    border-radius:8px; padding:0.3rem 0.75rem; font-size:0.68rem; color:#fbbf24;
    font-family:'JetBrains Mono',monospace; display:inline-flex; align-items:center; gap:0.4rem; }

/* Hint chips */
.hint-chips { display:flex; flex-wrap:wrap; gap:0.5rem; justify-content:center; margin:1.2rem 0 1.8rem; }
.hint-chip { background:rgba(10,5,30,0.8); border:1px solid rgba(168,85,247,0.15); border-radius:20px;
    padding:0.28rem 0.8rem; font-size:0.73rem; color:#64748b;
    cursor:pointer; transition:all 0.2s; font-family:'JetBrains Mono',monospace; }
.hint-chip:hover { border-color:#a78bfa; color:#a78bfa; }

/* Welcome glow */
.welcome-glow {
    font-size:3.4rem; font-weight:900; letter-spacing:-0.04em;
    background:linear-gradient(135deg,#c084fc 0%,#f0abfc 45%,#a78bfa 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    animation:welcomeGlow 3s ease-in-out infinite alternate;
    transition:opacity 0.6s ease-in-out;
}
@keyframes welcomeGlow {
    0%  { filter:drop-shadow(0 0 4px rgba(192,132,252,0.3)); }
    50% { filter:drop-shadow(0 0 18px rgba(168,85,247,0.6)); }
    100%{ filter:drop-shadow(0 0 6px rgba(240,171,252,0.35)); }
}
.axon-tagline { font-family:'JetBrains Mono',monospace; font-size:0.66rem;
    color:#334155; letter-spacing:0.2em; text-transform:uppercase; }
.axon-jp { font-family:'Noto Sans JP',sans-serif; font-size:0.68rem;
    color:rgba(249,168,212,0.35); letter-spacing:0.28em; margin-top:0.25rem; }

/* Inputs */
.stTextInput input, .stTextArea textarea {
    background: rgba(10,5,30,0.9) !important; border: 1px solid rgba(168,85,247,0.2) !important;
    border-radius: 12px !important; color: #e9d5ff !important;
    font-family: 'Space Grotesk', sans-serif !important; font-size: 0.88rem !important;
    padding: 0.7rem 1rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #7c3aed !important; box-shadow: 0 0 0 2px rgba(124,58,237,0.18) !important;
}
.stButton button {
    background: linear-gradient(135deg, #7c3aed, #9333ea) !important;
    border: none !important; border-radius: 10px !important; color: white !important;
    font-weight: 700 !important; font-family: 'Space Grotesk', sans-serif !important;
    padding: 0.5rem 1.6rem !important; font-size:0.86rem !important;
}
.stButton button:hover { opacity: 0.85 !important; }

/* Torii accent */
.torii-accent { display:flex; justify-content:center; opacity:0.1; margin:0.4rem 0; }

/* Scrollbar */
::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-track { background:#050810; }
::-webkit-scrollbar-thumb { background:rgba(168,85,247,0.3); border-radius:99px; }

/* Error badges */
.err-badge {
    font-family:'JetBrains Mono',monospace; font-size:0.6rem; font-weight:700;
    padding:0.13rem 0.48rem; border-radius:5px;
    background:#1a0a0a; color:#f87171; border:1px solid #3a1515;
}
</style>

<div class="jp-grid-bg"></div>
<canvas id="sakura-canvas"></canvas>
<script>
(function() {
  const canvas = document.getElementById('sakura-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let petals = [];
  function resize() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
  resize(); window.addEventListener('resize', resize);
  for (let i = 0; i < 30; i++) {
    petals.push({
      x: Math.random()*canvas.width, y: Math.random()*canvas.height,
      r: 2+Math.random()*3.5, vx: (Math.random()-0.5)*0.3,
      vy: 0.22+Math.random()*0.4, rot: Math.random()*Math.PI*2,
      vrot: (Math.random()-0.5)*0.018, alpha: 0.2+Math.random()*0.4
    });
  }
  function loop() {
    ctx.clearRect(0,0,canvas.width,canvas.height);
    for (let p of petals) {
      p.x+=p.vx; p.y+=p.vy; p.rot+=p.vrot;
      if (p.y > canvas.height+10) { p.y=-10; p.x=Math.random()*canvas.width; }
      if (p.x < -10) p.x=canvas.width+10;
      if (p.x > canvas.width+10) p.x=-10;
      ctx.save(); ctx.translate(p.x,p.y); ctx.rotate(p.rot); ctx.globalAlpha=p.alpha;
      ctx.fillStyle='#f9a8d4';
      ctx.beginPath(); ctx.ellipse(0,0,p.r,p.r*0.55,0,0,Math.PI*2); ctx.fill(); ctx.restore();
    }
    requestAnimationFrame(loop);
  }
  loop();
})();
</script>

<!-- Half cherry tree from ron.py original -->
<svg id="cherry-tree-deco" viewBox="0 0 320 1000" preserveAspectRatio="xMaxYMid slice" xmlns="http://www.w3.org/2000/svg">
  <path d="M320 1000 L320 600 C300 520 270 480 250 400 C235 340 245 260 220 200"
        stroke="#3a2a3a" stroke-width="18" fill="none" stroke-linecap="round"/>
  <path d="M320 700 C290 660 250 640 210 600 C180 570 170 520 150 480"
        stroke="#3a2a3a" stroke-width="10" fill="none" stroke-linecap="round"/>
  <path d="M320 450 C290 430 260 400 230 360"
        stroke="#3a2a3a" stroke-width="8" fill="none" stroke-linecap="round"/>
  <g fill="#f9a8d4">
    <circle cx="220" cy="200" r="60" opacity="0.5"/>
    <circle cx="150" cy="160" r="45" opacity="0.45"/>
    <circle cx="260" cy="120" r="50" opacity="0.45"/>
    <circle cx="180" cy="280" r="55" opacity="0.4"/>
    <circle cx="270" cy="320" r="48" opacity="0.38"/>
    <circle cx="120" cy="480" r="50" opacity="0.35"/>
    <circle cx="200" cy="550" r="44" opacity="0.32"/>
    <circle cx="280" cy="600" r="46" opacity="0.3"/>
    <circle cx="150" cy="650" r="40" opacity="0.28"/>
    <circle cx="240" cy="700" r="42" opacity="0.25"/>
  </g>
</svg>

<!-- Cherry petal canvas -->
<canvas id="cherry-petal-canvas"></canvas>
<script>
(function() {
  const canvas = document.getElementById('cherry-petal-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let petals = [];
  function resize() { canvas.width = canvas.offsetWidth; canvas.height = window.innerHeight; }
  resize(); window.addEventListener('resize', resize);
  for (let i = 0; i < 22; i++) {
    petals.push({
      x: Math.random()*canvas.width, y: Math.random()*canvas.height*0.5 - canvas.height*0.3,
      r: 2+Math.random()*3, vx: -0.2-Math.random()*0.4,
      vy: 0.4+Math.random()*0.6, rot: Math.random()*Math.PI*2,
      vrot: (Math.random()-0.5)*0.03, alpha: 0.35+Math.random()*0.4
    });
  }
  function loop() {
    ctx.clearRect(0,0,canvas.width,canvas.height);
    for (let p of petals) {
      p.x+=p.vx; p.y+=p.vy; p.rot+=p.vrot;
      if (p.y > canvas.height+10) { p.y=-10; p.x=canvas.width*0.4+Math.random()*canvas.width*0.6; }
      if (p.x < -10) p.x=canvas.width+10;
      ctx.save(); ctx.translate(p.x,p.y); ctx.rotate(p.rot); ctx.globalAlpha=p.alpha;
      ctx.fillStyle='#f9a8d4';
      ctx.beginPath(); ctx.ellipse(0,0,p.r,p.r*0.55,0,0,Math.PI*2); ctx.fill(); ctx.restore();
    }
    requestAnimationFrame(loop);
  }
  loop();
})();
</script>

<!-- Tiny monastery icons -->
<div class="monastery-deco">
  <svg width="44" height="44" viewBox="0 0 46 46" fill="none" xmlns="http://www.w3.org/2000/svg">
    <polygon points="23,4 40,16 6,16" fill="#a78bfa"/>
    <polygon points="9,16 37,16 39,26 7,26" fill="#a78bfa" opacity="0.85"/>
    <polygon points="5,26 41,26 43,38 3,38" fill="#a78bfa" opacity="0.65"/>
    <rect x="19" y="38" width="8" height="6" fill="#a78bfa" opacity="0.6"/>
    <rect x="21" y="0" width="3" height="6" fill="#a78bfa"/>
  </svg>
  <svg width="44" height="44" viewBox="0 0 46 46" fill="none" xmlns="http://www.w3.org/2000/svg">
    <line x1="6" y1="14" x2="40" y2="14" stroke="#c084fc" stroke-width="3" stroke-linecap="round"/>
    <line x1="4" y1="20" x2="42" y2="20" stroke="#c084fc" stroke-width="2" stroke-linecap="round"/>
    <line x1="13" y1="20" x2="13" y2="42" stroke="#c084fc" stroke-width="3" stroke-linecap="round"/>
    <line x1="33" y1="20" x2="33" y2="42" stroke="#c084fc" stroke-width="3" stroke-linecap="round"/>
  </svg>
  <svg width="44" height="44" viewBox="0 0 46 46" fill="none" xmlns="http://www.w3.org/2000/svg">
    <polygon points="23,6 38,18 8,18" fill="#f0abfc" opacity="0.9"/>
    <polygon points="10,18 36,18 38,28 8,28" fill="#f0abfc" opacity="0.7"/>
    <rect x="19" y="28" width="8" height="14" fill="#f0abfc" opacity="0.6"/>
    <rect x="21" y="0" width="3" height="6" fill="#f0abfc"/>
  </svg>
</div>
""", unsafe_allow_html=True)



for key, val in {
    "page": "home",
    "chat_history": [],
    "api_keys": [k for k in DEFAULT_API_KEYS if k and not k.startswith("AIzaSy_REPLACE")],
    "current_task": "",
    "pipeline_done": False,
    "pipeline_data": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = val



with st.sidebar:
    st.markdown('<div class="sidebar-logo">🌸 Axon - Nexus</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Multi-Agentic Infrastructure · Quantum OS · 2026</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-jp">星の量子知性システム · 東京</div>', unsafe_allow_html=True)

    # Locked profile card
    st.markdown(f'''
    <div style="display:flex;align-items:center;gap:0.6rem;background:rgba(10,5,30,0.9);
                border:1px solid rgba(168,85,247,0.2);
                border-radius:12px;padding:0.6rem 0.8rem;margin-bottom:1rem;">
      <div style="width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;
                  font-weight:900;font-size:0.95rem;color:white;flex-shrink:0;
                  background:linear-gradient(135deg,#7c3aed,#db2777);">{BUILDER["initials"]}</div>
      <div style="line-height:1.3;min-width:0;">
        <div style="font-size:0.78rem;font-weight:700;color:#e9d5ff;">{BUILDER["name"]}</div>
        <div style="font-size:0.6rem;color:#7c5ea8;font-family:'JetBrains Mono',monospace;
                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{BUILDER["email"]}</div>
      </div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown("---")

    # Navigation
    pages = [
        ("home",     "", "Dashboard"),
        ("agents",   "", "Agent Mesh"),
        ("workflow", "⚛",  "Quantum Workflow"),
        ("builder",  "👤", "Builder Info"),
        ("help",     "", "Customer Help"),
        ("settings", "⚙️", "Settings"),
    ]
    for pid, icon, label in pages:
        active = "active" if st.session_state.page == pid else ""
        if st.button(f"{icon}  {label}", key=f"nav_{pid}", use_container_width=True):
            st.session_state.page = pid
            st.rerun()

    st.markdown("---")
    st.markdown('<div style="font-size:0.62rem;color:#3b2a5a;font-family:\'JetBrains Mono\',monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.4rem;">INDIA GATE</div>', unsafe_allow_html=True)
    st.markdown('<img src="data:image/png;base64,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iysxLtlahCGYsDrte36TfbqF65xaxrnOdYAXJOwWkpCFMUXEEGqSsHO+AXcNyA4FpBHvXr4OJKtPSr4UxBgsEQFpDQdiLEIPsm8VRJyNFgyMuwSuretfqXjvA5BfEwcC4oEBsNvCuYBAREQEREBRWyXQQ7oFSogDdBuitkESyIN0AbordRBCpf6qyUs763tQZIiICIiAiIgWSyJZACIiAiIgWSyJZAsiIgLF7M3aWSIPmdKQ3eauSFBa3srlslkDKuB8u13mrnRBww5drey1ctuBVEHE+A13aasGy7W9lq+iyII1qxfCa7tLMIg4RLQ2+auRrcqyRBjEY1zFweSQ8+bKvpUO6DBkLKsi3MsgiDgdLQ3eas2QmtXIiDGywfAhu7TVyoEHzGUh/RWbILW9lq5rJZBjlXG6BDd5q5kQfP5ND+i1cjITW9lciWQY2XDEl4bvNX0WSyDghy7W9lq5QFkEQcUSC2J2mrBktDb2WtX0IgxDVxxILYnaXMUsg+ZkpDb5vEudrcqysiDjfDa5cYlYefshfQlkGLWZVIkNrlmiD5xKw8+bKuZjMrFkiDB7WuXEZWH9FfQiDjZDa3sqlizRB87paG7zVmyC1vZauVEEDVxPlobvNXOEug4Wwmt7KzLVkUQcT5eG7zWqshNb2VyIQggCqIgIiICIlkBLIAhQFDul0QEsoSqgoUVQoIl1CVUBY/5vsVJUsgzREQAgREBERAQoiAiBEBLogQAiK2QRERAREQEREBFbKICIiAiIgIiICIiAiIUBERAREQEREBFQFEBERAREQERUhBEREBERAJREQEVCiAiIgIiICIiAiIgIERARWyiAitlEBERARFbIIiIgFEuiAgRWyCIUKIIN0VsoUBBuioCAhREEO6hCtksggU/ytWSxy/V96DNERAREQERCgIrZRAREQEREBFbKICIhQEREBERBSoiICIiAiIgtlERAKFLogIiICIiAiXRAREQEVsogIiICIiArZREBERAREQFbKIgIiFAREQEREBEQoCIiAiIgIiICJdEBERAREQEQpdARFbIIiKkIIiFAgAohCAIACAIiAiKIFkRUoIn+lBumb4sgqIiAiIgIiICIiAiIgWRAiAiIgAoiICIiAiIgIiICIiAiIgIiICIEQEQogIiWQEQogIiICIiAiWQoCIiAiIgJdEQEREBERAREsgIiICIiAiJZAREQEREBERAREQFSoiAiIgFERAREQEREBEsiAAiAogJdEQERCgEKXVUKBdEWNv4UGaIiAiIgIiICIiAiBEBEQoCWQogAJZAiAiIgIURAslkCICIiAiFECyWREBERAREKBZLJZECyBEQEREBSyqIFkCIgIiXQClkRASyIgIURAQoiBZERAREQEIRECyWREBERAREQLIgRAsiBEBEQoCWREBAiICIiAURECyIAiAiFEAlAil0BLJZEFKFCoUEup/l96KXQciBEugIiIAREQEREBERAREQEKIgIiICIiBdERAREQEREBERAREQEQogBERAREQEREBCiICWREBERAREQEREBERAREQEuiICIrZBEREC6Il0BERAREQLoiIF0REBFbKICBEQEREBERAREQECIgIiICh3VSyCXSyHdAgICiFAsiIghWPF9L3LNYW+LoORLIiAiIgIiICIiAiIgIiICIiAiIgIiICIiC2QJZRAREQEREBWyiIBREQEKKhBFQoiAiIgWREQEREFsoiICIiAiIgtlERAREQEREBERAREQEREBFQogIiICIiAqVEQERCgIiICtlEQEREC6IiArZREBERAQFEsgWUAWRUQSyKlRAsiqgQQp/lVU/wAqDJCUUO6CgoFiQsrICIiAiIgIiICIiAiIgIiICIiAiIgIiFARLIgIiICIUQEREBERARCiAiIgIiICIiAiIgIit0ERW6iAiIgIiICIiAiIgIiICIrdBEREBERAREQEQogIlkQEREBERAREQEREBERAREQEKhVQCgQlEBRVRAQ7oN0QFLKqW/iQZJZCiAiIgIiICIhQERAgIgKICIiAiIgIiICIlkBLIgQAiIgIiICIUsgIiICIhKAiJZAsiIgIiICIiBZERAREQEREBERAREQEREBLolkCyIiAiIgIiICIiAiIUBCiFAREQEREBEsiAiEIgIiICIiApZVAgIhKIJZLKkqWQEREBECHdAUzfwqrG7fooM0QIgIiICJZEBERAREQEREBAiIAREQEREBCl0QAiIgIiFAuiJdARLogh3VQhS6CpdREFuiAogIiICXREBAUQICIiAiIgIEQFAREQEREAoiICIgQEREBEJS6AiIgIiICIl0BERACIiAiIgXRAiBZERAKipUQS6yusQgKClVQbqoCgRLoFkVupdBAVURARFCgqxs5UqIM0RCgIl0QEREBERARUqIBS6WQICIqEEREQEREBERARWyWQCoqVCgAohRARWyiASohRAREQAqgRAREQEREBEVsgiIiAiIgXREQEREBCiXQCEREBAiICIiBdERAREQEREBERARFSEERWyiAiIgIgVsgiIiA5YkrIrEBBUG6oCICK2UQREO6IF0UBVCAUQogIoFUBYcP1lkVLfF0GYKKKoBREQEREBCURAJRQogqIiAiIgIiICIiAiIgIiIF0uod0QUFFBusroIiIgiIiAiIgDdVQbqlARQbqgoCIiAl0JUugqIEQEREFBUREBFbqICIiAiBW6CIiIFkREBERARW6iAhREBERAREQEREAIiICoS6iAiIghQbogQVUqK3QRLpdRARUKIICgKqICIiAoSgVQFLKrD/AE+5BmFSFLKoBRQKoCIiC3UKKXQEREFCKDdVBbqIiAiIgIiIKEuoiAlkRBLIqlkAK3URAREQYkKoUQEG6HdEFCFLrG6ClUJdEBW6iICxJWRCh3QFVFQEAIiILdREQEREBERBbpdRLoCIiAiBEBERARLIgIiILdLqIgIhRAREQFbqIgt1CiICWREEsqiILdRcsszNFb9EalYx25Yrm/FkGBKIod0BQlUod0A7oiIISqigQLJZVEEKxt8WWVlP9SDJEO6hKDJAoN1UBAiIBKit1CgllUslkBUKFWyAiIgIiICFEQEREBAUuiAiIgIiIF0RAgIUQhBERLIIECqIAVUVQEQFLoCFS6AoLZERAREQEQlEBERAREQERLoCIiAiIgIiFAS6BEBERAQohQECIgIiICIiAiIgBERAVY1zn5WrKE2G7945zV90JkNrPm8vpQSDD6tn1uaxmIfWM+sNvwXKiDrSHN4XLELsIrYbmfOZfTsviithtf8ANuzelBgUREBERBCllVCgAqoiAsbrJY8X1kGSIoEFG6oCit0BES6AiIgIiICIiASsbrIqIF1QoN0QVFLqoF0uiICIiAiIgXS6IgXQBEQEREEO6qIUERVEECtkRAUuhRBAVUG6WQUIiXQEJUuoCgyQKBVAREQEREBLoiAiIgIiICIiAiIgIiICIiAiIgIiICXRQoLdFLqgoCBCoEFBWcOK6G/h9nIrBCg7CE9sRmZv9FI0RsNmb2BfNJvyxcvmv+1SafmjfVGgQcb4joj8zv5LEKlRAUKqIJdVQqoF0REAboiIISnEqiAiIghVuoUugp3REKCooFldBEVuogIiICl1VEBEuh3QEREAK3Usl0FCKXVCAiIgIl0QECIUBQJdLICoCgRAssrqKXQVECEoMSVURAREQEuiFAREQQFZKJdBUVuogIiICIl0FCiXQICJdEBERARArdBEQlLoFkREBECEoCKXQoKod0RAsqoqEApZEQLIiICXRRAO6lkKBBUREBERBAqiIChVRAWNkWN2/RQcihVUP8KAFFksUGSLFZIF1QViVUC6qxaqCgqBCUCASoVSVLoCIiAiIgIioQRVEQEREAJdEugFS6risSUAqqFVAsrdAlkBEuiCIqQpZARBuiAN0uiICIiAoAqiAiHdLoF1bqIgt0KiXQLoUsh3QEREBUFRAgqIiAhKIgiIiAN1Sod0QLoiICDdS6yCBZLIiAFbqIgIlkCAl0RAWJKp3RARQFVAUsqoCgqIiAihUJQUlVYoQgKHdUlTiQZqFLqICIQiChAqoUApZAqglkBVRBboCoiAUQFEEKqIgIiICDdEQW6IiBZLood0C6qiIDioUJUQAVbqArJBAqiIKECgKt0C6BY3WQCCFFVCgIlkQEREBERAREQEREBECHdAQ7od1CUFREQFbKWVQERCgIUuiCIqhCCIiICIiAqAoN1UBERAREugIiXQCVLKoEERQFVAUsqiAiIgIoUCAVFbKICIskGNkyq2ThQVYogCC3QoFEBUIVUBQKK3QVERARS6BBEVsqgxIWShVAQEUIVQEUuhQW6XREFCFRAghCBHIUFKxVKiAskRBiiIgt0uoQskEIVCDdAgqXREBEuiAiIglkQogIiICBFQgAJZEQLJZEugWSyIgIiICIiAiFCUBFCiAiIgIiIKEUCqAiJdAS6EpZABWLlQpdBUQ7ogKEpdVARQKoIFUUKCqBCogoUVKWQCqpZCgBY3+sqr8ckEREQAVksUOyAiAqXQVZLFZIIFVAl0EREAQWyqIghVUCXQVwUCFVBCEKBQlBQqUUugqIpdBUUIVQYrJS6iC2QqIgIiIKUul1UBEUugqEod0QDugUJVQLoiICIiAiIgKhRLoKiXQlARS6AoKiIgIiICJdLoIUQogIiICIiAg3RUIARLpdARLqXQVFiEugH6Kql0ugqxVKqAigS6AEKXS6CopdCgiK3UBQAERZIChVUugWU4vpKlS3xYoP/Z" style="width:100%;border-radius:8px;" />', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;font-family:\'JetBrains Mono\',monospace;font-size:0.6rem;color:rgba(196,166,255,0.4);letter-spacing:0.15em;margin-bottom:0.8rem;">NEW DELHI · INDIA</div>', unsafe_allow_html=True)

    nkeys = len(st.session_state.api_keys)
    color = "#34d399" if nkeys > 0 else "#f87171"
    st.markdown(f'<div style="font-size:0.66rem;color:{color};font-family:\'JetBrains Mono\',monospace;margin-top:0.4rem;">● System Active</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div style="font-size:0.6rem;color:#3b2a5a;font-family:\'JetBrains Mono\',monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.35rem;">Error Codes</div>', unsafe_allow_html=True)
    for code, desc in [
        ("AX-401","Invalid key"),("AX-403","No model access"),
        ("AX-404","Model not found"),("AX-429","Rate limit → rotate"),
        ("AX-500","Server error → retry"),("AX-503","Overloaded → retry"),
        ("AX-000","Unknown"),("AX-KEY","All keys exhausted"),
    ]:
        st.markdown(f'<div style="display:flex;gap:0.4rem;align-items:center;margin:0.12rem 0;"><span class="err-badge">{code}</span><span style="font-size:0.63rem;color:#475569;">{desc}</span></div>', unsafe_allow_html=True)

    
    st.markdown("---")
    st.markdown('<div style="font-size:0.6rem;color:#3b2a5a;font-family:\'JetBrains Mono\',monospace;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.4rem;">System Status</div>', unsafe_allow_html=True)
    st.markdown(f'''
    <div style="display:flex;flex-direction:column;gap:5px;font-size:0.7rem;">
      <div style="display:flex;justify-content:space-between;">
        <span style="color:#a78bfa;">DWSA Core</span>
        <span style="color:#86efac;display:flex;align-items:center;gap:4px;"><span class="status-dot"></span> Online</span>
      </div>
      <div style="display:flex;justify-content:space-between;">
        <span style="color:#a78bfa;">Quantum Layer</span>
        <span style="color:#c4b5fd;">Processing</span>
      </div>
      <div style="display:flex;justify-content:space-between;">
        <span style="color:#a78bfa;">Agents Active</span>
        <span style="color:#e9d5ff;font-weight:700;">7</span>
      </div>
    </div>
    ''', unsafe_allow_html=True)



def safe_json(raw):
    text = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
    text = re.sub(r",\s*([}\]])", r"\1", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"[\[{].*[\]}]", text, re.DOTALL)
        if m:
            return json.loads(m.group())
        raise


def quantum_route_order(n_tasks, weights):
    qc = QuantumCircuit(n_tasks, n_tasks)
    for i in range(n_tasks):
        qc.h(i)
        angle = float(weights[i]) * math.pi
        qc.ry(angle, i)
    for i in range(n_tasks - 1):
        qc.cx(i, i + 1)
    qc.measure(range(n_tasks), range(n_tasks))
    sim = AerSimulator()
    tqc = transpile(qc, sim)
    job = sim.run(tqc, shots=512)
    counts = job.result().get_counts()
    qubit_ones = [0] * n_tasks
    total = sum(counts.values())
    for bitstring, count in counts.items():
        bits = bitstring.replace(" ", "")
        for qi in range(n_tasks):
            pos = len(bits) - 1 - qi
            if pos >= 0 and bits[pos] == "1":
                qubit_ones[qi] += count
    scores = [c / total for c in qubit_ones]
    order = sorted(range(n_tasks), key=lambda i: scores[i], reverse=True)
    return order, {
        "n_qubits": n_tasks, "shots": 512,
        "top_states": dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]),
        "qubit_scores": [round(s, 4) for s in scores],
        "order": order,
    }


def render_torii():
    st.markdown("""
<div class="torii-accent">
<svg width="100" height="45" viewBox="0 0 100 45" xmlns="http://www.w3.org/2000/svg">
  <line x1="8" y1="12" x2="92" y2="12" stroke="#a78bfa" stroke-width="4" stroke-linecap="round"/>
  <line x1="4" y1="19" x2="96" y2="19" stroke="#a78bfa" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="22" y1="19" x2="22" y2="45" stroke="#a78bfa" stroke-width="3" stroke-linecap="round"/>
  <line x1="78" y1="19" x2="78" y2="45" stroke="#a78bfa" stroke-width="3" stroke-linecap="round"/>
  <line x1="25" y1="27" x2="75" y2="27" stroke="#a78bfa" stroke-width="1.5" opacity="0.5" stroke-linecap="round"/>
</svg>
</div>""", unsafe_allow_html=True)



def render_quantum_sphere(state="idle", agent_count=0, label=""):
    pal_map = {"idle":"violet","thinking":"aurora","routing":"cosmic","verifying":"aurora","complete":"cyan"}
    lbl_map = {"idle":"HOSHI · STANDBY","thinking":"AGENT SWARM · THINKING",
               "routing":"QUANTUM ROUTING","verifying":"SELF-AUDITING","complete":"PIPELINE · COMPLETE"}
    palette  = pal_map.get(state, "violet")
    disp_lbl = label if label else lbl_map.get(state, "HOSHI CORE")
    badge = ""
    if agent_count > 0:
        badge = f"""<div style="position:absolute;top:12px;right:16px;z-index:10;
                    background:rgba(5,2,15,0.85);border:1px solid rgba(168,85,247,0.4);
                    border-radius:10px;padding:5px 12px;text-align:center;
                    font-family:'JetBrains Mono',monospace;line-height:1.3;">
          <div style="font-size:17px;font-weight:900;color:#c084fc;">{agent_count}</div>
          <div style="font-size:8px;color:#64748b;letter-spacing:0.12em;">AGENTS</div>
        </div>"""

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#03010a;overflow:hidden;width:100%;height:100%;}}
canvas{{display:block;position:absolute;top:0;left:0;width:100%;height:100%;}}
#label{{position:absolute;bottom:10px;left:50%;transform:translateX(-50%);
  font-family:'JetBrains Mono',monospace;font-size:9px;font-weight:700;
  color:rgba(192,132,252,0.8);letter-spacing:3px;text-transform:uppercase;
  white-space:nowrap;pointer-events:none;}}
{badge}
</style></head><body>
<canvas id="c"></canvas>
<div id="label">{disp_lbl}</div>
<script>
const cvs=document.getElementById('c'),ctx=cvs.getContext('2d');
function resize(){{cvs.width=cvs.offsetWidth;cvs.height=cvs.offsetHeight;}}
resize();window.addEventListener('resize',resize);
const palettes={{
  violet:{{glow:'192,132,252',core:'216,180,254'}},
  aurora:{{glow:'240,171,252',core:'245,208,254'}},
  cyan:{{glow:'52,211,153',core:'110,231,183'}},
}};
const N=360,pts=[];
for(let i=0;i<N;i++){{
  const phi=Math.acos(1-2*(i+0.5)/N),theta=Math.PI*(1+Math.sqrt(5))*i;
  pts.push({{ox:Math.sin(phi)*Math.cos(theta),oy:Math.cos(phi),oz:Math.sin(phi)*Math.sin(theta),
    phase:Math.random()*Math.PI*2,
    cg:`hsla(${{Math.random()*360}},80%,70%,0.9)`,cc:`hsla(${{Math.random()*360}},100%,85%,1)`}});
}}
let rX=0,rY=0,tX=0,tY=0,vX=0,vY=0,drag=false,mx=0,my=0,wobble=0,t=0;
const pal='{palette}';
function rot(x,y,z,rx,ry){{
  let y2=y*Math.cos(rx)-z*Math.sin(rx),z2=y*Math.sin(rx)+z*Math.cos(rx);
  let x2=x*Math.cos(ry)+z2*Math.sin(ry),z3=-x*Math.sin(ry)+z2*Math.cos(ry);
  return[x2,y2,z3];
}}
function frame(){{
  t+=0.012;wobble*=0.95;vX*=0.88;vY*=0.88;
  if(!drag){{tY+=0.003+wobble*0.01;tX+=wobble*0.008;}}
  rX+=(tX-rX)*0.07;rY+=(tY-rY)*0.07;
  const W=cvs.width,H=cvs.height,cx=W/2,cy=H/2,R=Math.min(W,H)*0.36;
  ctx.clearRect(0,0,W,H);
  const proj=pts.map(p=>{{
    const pulse=1+0.04*Math.sin(t*1.5+p.phase);
    const[rx,ry,rz]=rot(p.ox*pulse,p.oy*pulse,p.oz*pulse,rX,rY);
    return{{sx:cx+rx*R,sy:cy+ry*R,z:rz,cg:p.cg,cc:p.cc}};
  }});
  const sorted=Array.from({{length:proj.length}},(_,i)=>i).sort((a,b)=>proj[a].z-proj[b].z);
  sorted.forEach(idx=>{{
    const p=proj[idx];
    const alpha=Math.max(0.12,(p.z+1.2)/2.2);
    const ds=Math.max(1.2,(p.z+1.2)*2.8);
    let glow,core;
    if(pal==='cosmic'){{glow=p.cg;core=p.cc;}}
    else{{const pl=palettes[pal]||palettes.violet;glow=`rgba(${{pl.glow}},${{alpha}})`;core=`rgba(${{pl.core}},${{alpha}})`;}}
    const gr=ds*3.2;
    const g=ctx.createRadialGradient(p.sx,p.sy,ds*0.1,p.sx,p.sy,gr);
    g.addColorStop(0,glow);g.addColorStop(0.3,glow);g.addColorStop(1,'rgba(0,0,0,0)');
    ctx.fillStyle=g;ctx.beginPath();ctx.arc(p.sx,p.sy,gr,0,Math.PI*2);ctx.fill();
    ctx.fillStyle=core;ctx.beginPath();ctx.arc(p.sx,p.sy,ds*0.65,0,Math.PI*2);ctx.fill();
  }});
  requestAnimationFrame(frame);
}}
window.addEventListener('mousedown',e=>{{drag=true;mx=e.clientX;my=e.clientY;tX=rX;tY=rY;}});
window.addEventListener('mousemove',e=>{{
  if(!drag)return;
  const dx=e.clientX-mx,dy=e.clientY-my;
  vX=dx*0.0015;vY=dy*0.0015;tY+=vX;tX+=vY;mx=e.clientX;my=e.clientY;
}});
window.addEventListener('mouseup',()=>drag=false);
window.addEventListener('dblclick',()=>wobble=0.45);
frame();
</script></body></html>"""
    components.html(html, height=300, scrolling=False)




class QuantumBrain:
    def __init__(self):
        self.entries = []; self.read_count = 0; self.write_count = 0

    def write(self, agent_id, title, content, importance=0.8):
        self.entries.append({"agent_id":agent_id,"title":title,"content":content,
            "timestamp":datetime.now().strftime("%H:%M:%S.%f")[:-3],"importance":round(importance,2)})
        self.write_count += 1

    def read_context(self, exclude_agent=""):
        relevant = [e for e in self.entries if e["agent_id"] != exclude_agent]
        self.read_count += 1
        if not relevant: return "(Brain empty — first agent)"
        return "\n\n".join(f"[{e['agent_id']} @ {e['timestamp']}] {e['title']}\n{e['content']}" for e in relevant)

    def render_html(self):
        if not self.entries:
            return '<div class="brain-entry" style="color:#475569;font-style:italic">No entries yet…</div>'
        html = ""
        for e in self.entries:
            html += f"""<div class="brain-entry">
              <span style="font-family:'JetBrains Mono',monospace;font-size:0.58rem;color:#34d399;background:rgba(52,211,153,0.08);padding:0.08rem 0.35rem;border-radius:4px;margin-right:0.35rem;">AGENT-{e['agent_id']}</span>
              <span style="color:#e2e8f0;font-weight:600">{e['title']}</span>
              <span style="color:#475569;font-family:'JetBrains Mono',monospace;font-size:0.56rem;margin-left:0.35rem">{e['timestamp']}</span>
              <span style="font-family:'JetBrains Mono',monospace;font-size:0.54rem;color:#f9a8d4;background:rgba(249,168,212,0.08);padding:0.06rem 0.3rem;border-radius:4px;margin-left:0.25rem;">IMP {e['importance']:.2f}</span>
              <div style="margin-top:0.18rem;color:#94a3b8;font-size:0.72rem">{e['content'][:200]}{'…' if len(e['content'])>200 else ''}</div>
            </div>"""
        return html



def stage_dwsa(keys, task):
    system = ("You are DWSA — Divisible Work Sharing Agent. "
        "Decompose ANY user task into exactly 4–6 atomic, non-overlapping subtasks. "
        'Return ONLY a JSON array: [{"id":1,"title":"...","description":"...","priority_weight":0.0-1.0},...]. No markdown, no prose.')
    return safe_json(gemini_json(keys, f"Decompose this task into subtasks: {task}", system))

def stage_quantum_routing(subtasks):
    weights = [s.get("priority_weight", 0.5) for s in subtasks]
    order_indices, meta = quantum_route_order(len(subtasks), weights)
    meta["ordered_ids"] = [subtasks[i]["id"] for i in order_indices]
    return meta["ordered_ids"], meta

def spawn_agent(keys, agent_id, subtask, overall_task, brain):
    brain_context = brain.read_context(exclude_agent=agent_id)
    system = (f"You are Agent-{agent_id}, a specialist AI for subtask '{subtask['title']}'. "
        "Use the Quantum Brain context to avoid redundancy. Be structured, precise, and complete.")
    prompt = (f"OVERALL GOAL: {overall_task}\n\nYOUR SUBTASK ({subtask['id']}): {subtask['title']}\n"
        f"Description: {subtask['description']}\n\n━━ QUANTUM BRAIN CONTEXT ━━\n{brain_context}\n━━━━━━━━━━━━\n\nExecute your subtask:")
    output = gemini_text(keys, prompt, system)
    brain.write(agent_id, subtask["title"], output, importance=min(0.6+subtask.get("priority_weight",0.5)*0.4,1.0))
    return output

def stage_synthesis(keys, task, brain):
    system = ("You are the Hoshi Brain Synthesiser. Synthesise all agent outputs into one coherent, "
        "comprehensive response that fully answers the original task. Integrate insights, avoid repetition.")
    return gemini_text(keys, f"ORIGINAL TASK: {task}\n\n━━ BRAIN DUMP ━━\n{brain.read_context()}\n━━━━━━━━━\n\nSynthesise:", system)

def stage_critic(keys, task, synthesised, brain):
    system = ('You are the Critic Agent. Analyse the synthesised response. Return ONLY JSON:\n'
        '{"contradictions":["..."],"weak_reasoning":["..."],"missing_info":["..."],'
        '"revision_requests":["..."],"critic_score":0-100,"verdict":"PASS|REVISE|FAIL"}\nNo markdown.')
    raw = gemini_json(keys, f"TASK: {task}\n\nRESPONSE:\n{synthesised}\n\nCritique:", system)
    result = safe_json(raw)
    brain.write("CRITIC", "Critic Analysis", json.dumps(result, indent=2), importance=0.95)
    return result

def stage_verifier(keys, task, synthesised, critic, brain):
    system = ('You are the Verification Agent. Return ONLY JSON:\n'
        '{"consistency_check":"PASS|PARTIAL|FAIL","completeness_score":0-100,'
        '"verification_score":0-100,"issues":["..."],"strengths":["..."],'
        '"final_verdict":"VERIFIED|NEEDS_WORK|FAILED"}\nNo markdown.')
    prompt = (f"TASK: {task}\n\nRESPONSE:\n{synthesised}\n\n"
        f"CRITIC SUMMARY: {json.dumps({'score':critic.get('critic_score',0),'verdict':critic.get('verdict','?')})}\n\nVerify:")
    raw = gemini_json(keys, prompt, system)
    result = safe_json(raw)
    brain.write("VERIFIER", "Verification Report", json.dumps(result, indent=2), importance=0.95)
    return result

def stage_seo(keys, synthesised, task):
    system = ('You are the SEO Optimisation Agent. Return ONLY JSON:\n'
        '{"seo_title":"...","meta_description":"...","keywords":["kw1","kw2",...],'
        '"optimised_content":"...","seo_score":0-100,"readability_score":0-100,'
        '"keyword_density":0.0-1.0,"word_count":integer}\nNo markdown.')
    return safe_json(gemini_json(keys, f"Topic: {task}\n\nContent:\n{synthesised}", system))

def compute_confidence(critic, verifier, brain, n_agents):
    c = critic.get("critic_score", 70); v = verifier.get("verification_score", 70)
    m = min(100, len(brain.entries) / max(n_agents, 1) * 20)
    bonus = 10 if verifier.get("final_verdict") == "VERIFIED" else 0
    return round(min((c*0.35 + v*0.40 + m*0.15 + bonus)*0.9 + 5, 99), 1)

def compute_ap(resonance, seo_score, n_subtasks):
    return round(resonance * seo_score / 100 * math.log1p(n_subtasks) * 10, 3)



STAGES = [
    ("LAYER 01", "DWSA Decomposer - Divisible Work sharing agentic orchestration",   "Breaks task into 4–6 atomic subtasks"),
    ("LAYER 02", "Quantum Router",     "Qiskit circuit determines execution order"),
    ("LAYER 03", "Agent Swarm",        "N specialist agents run in quantum order"),
    ("LAYER 04", "Brain Synthesis",    "Synthesiser unifies complete memory"),
    ("LAYER 05", "Critic + Verifier",  "Self-critic & verifier agents audit output"),
    ("LAYER 06", "SEO Agent",          "Optimises, scores & finalises content"),
]

def render_stages(stage_states):
    for i, (label, title, desc) in enumerate(STAGES):
        s = stage_states[i] if i < len(stage_states) else "pending"
        st.markdown(f"""
        <div class="pipe-card {s}">
            <div class="pipe-label">{label} · {s.upper()}</div>
            <div class="pipe-title">{title}</div>
            <div class="pipe-body">{desc}</div>
        </div>""", unsafe_allow_html=True)

def render_reasoning_graph(subtasks, active_idx=-1, critic_done=False, verifier_done=False, synthesis_done=False):
    n = len(subtasks)
    nodes_html = '<div style="display:flex;justify-content:center;margin-bottom:0.25rem"><div style="background:rgba(124,58,237,0.15);border:1px solid rgba(168,85,247,0.3);border-radius:8px;padding:0.25rem 0.85rem;font-family:\'JetBrains Mono\',monospace;font-size:0.66rem;color:#a78bfa;font-weight:700;">⚛ TASK</div></div>'
    nodes_html += '<div style="display:flex;justify-content:center;margin-bottom:0.25rem"><div style="width:2px;height:14px;background:rgba(168,85,247,0.2);margin:auto;"></div></div>'
    colors = []
    for i in range(n):
        if i < active_idx:   colors.append(("#34d399","rgba(13,42,31,0.8)","#153a15"))
        elif i == active_idx: colors.append(("#c084fc","rgba(13,5,30,0.8)","rgba(168,85,247,0.4)"))
        else:                  colors.append(("#2d3748","rgba(13,10,28,0.8)","rgba(45,39,72,0.5)"))
    nodes_html += '<div style="display:flex;gap:0.45rem;justify-content:center;flex-wrap:wrap;">'
    for i, s in enumerate(subtasks):
        c, bg, border = colors[i]
        nodes_html += f'<div style="background:{bg};border:1px solid {border};border-radius:8px;padding:0.25rem 0.65rem;font-size:0.64rem;color:{c};font-family:\'JetBrains Mono\',monospace;text-align:center;min-width:75px;">{s["id"]}. {s["title"][:18]}</div>'
    nodes_html += '</div>'
    extras = []
    if synthesis_done: extras.append(("🧠","#a78bfa","SYNTHESIS"))
    if critic_done:    extras.append(("🔍","#f87171","CRITIC"))
    if verifier_done:  extras.append(("✅","#34d399","VERIFIER"))
    if extras:
        nodes_html += '<div style="display:flex;gap:0.55rem;justify-content:center;margin-top:0.45rem;">'
        for icon, c, lbl in extras:
            nodes_html += f'<div style="background:rgba(10,5,30,0.8);border:1px solid {c}44;border-radius:8px;padding:0.22rem 0.65rem;font-size:0.63rem;color:{c};font-family:\'JetBrains Mono\',monospace;">{icon} {lbl}</div>'
        nodes_html += '</div>'
    st.markdown(f'<div style="background:rgba(6,3,20,0.9);border:1px solid rgba(168,85,247,0.12);border-radius:12px;padding:0.75rem;">{nodes_html}</div>', unsafe_allow_html=True)



page = st.session_state.page

if page == "home":
    render_torii()
    st.markdown("""
    <div style="max-width:780px;margin:0 auto;">
      <div style="text-align:center;padding:2.5rem 0 1.8rem;">
        <div class="welcome-glow" id="welcome-text">Welcome  Hoshi</div>
        <div class="axon-tagline">Autonomous AI · Quantum Workflow · OS 2026 · Version 7.0.341</div>
        <div class="axon-jp">量子自律型AIオペレーティングシステム · 東京</div>
      </div>
    </div>
    <script>
    (function(){
      const el=document.getElementById('welcome-text');if(!el)return;
      const msgs=["Welcome back, Hoshi","おかえり、星","Hoshi · Quantum Core Active"];
      let i=0;
      setInterval(function(){
        i=(i+1)%msgs.length;el.style.opacity=0;
        setTimeout(function(){el.textContent=msgs[i];el.style.opacity=1;},600);
      },4000);
    })();
    </script>
    """, unsafe_allow_html=True)

    # Quick stats
    st.markdown("""
    <div style="display:flex;gap:12px;justify-content:center;margin-bottom:1.2rem;flex-wrap:wrap;">
      <div class="metric-box"><div class="metric-val">7</div><div class="metric-lbl">Agents Active</div></div>
      <div class="metric-box"><div class="metric-val" style="color:#34d399">99.4%</div><div class="metric-lbl">Uptime</div></div>
      <div class="metric-box"><div class="metric-val" style="color:#fbbf24">2.1ms</div><div class="metric-lbl">Latency</div></div>
      <div class="metric-box"><div class="metric-val" style="color:#f472b6">∞</div><div class="metric-lbl">Quantum States</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div style="max-width:780px;margin:0 auto;"><div class="chat-bubble-user">{msg["content"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="max-width:780px;margin:0 auto;"><div class="chat-bubble-axon"><div class="axon-avatar">HOSHI · AXON</div>{msg["content"]}</div></div>', unsafe_allow_html=True)

    if not st.session_state.chat_history:
        render_quantum_sphere("idle", 0, "HOSHI · STANDBY")
        st.markdown("""
        <div style="max-width:780px;margin:0 auto;">
        <div class="hint-chips">
          <div class="hint-chip">📝 Write a report on AI trends</div>
          <div class="hint-chip">🔬 Explain quantum computing</div>
          <div class="hint-chip">🌸 Research Japanese robotics</div>
          <div class="hint-chip">🤖 Design a multi-agent system</div>
          <div class="hint-chip">📊 Analyse renewable energy market</div>
          <div class="hint-chip">🏙️ Compare Tokyo & Delhi tech ecosystems</div>
        </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_input = st.text_input("Message Hoshi", placeholder="Ask anything — Hoshi will deploy its quantum agent swarm…",
                                   label_visibility="collapsed", key="chat_input")
    with col_btn:
        send = st.button("Send →", use_container_width=True)

    if send and user_input.strip():
        if not st.session_state.api_keys:
            st.error("⚠️ [AX-KEY] No API keys configured in the system pool.")
        else:
            task = user_input.strip()
            st.session_state.current_task = task
            st.session_state.pipeline_done = False
            st.session_state.pipeline_data = {}
            st.session_state.chat_history.append({"role":"user","content":task})
            st.session_state.chat_history.append({"role":"axon","content":f"""
<div class="processing-card">
  <div class="processing-title">🌸 Your request is being processed through Hoshi's quantum pipeline</div>
  <div class="processing-sub">
    Deployed across <b style="color:#c084fc">6 pipeline layers</b> · Qiskit routing active · Specialist agents spawning<br>
    <span style="color:#a78bfa;font-family:'JetBrains Mono',monospace;font-size:0.73rem;">Task: {task[:80]}{'…' if len(task)>80 else ''}</span>
  </div>
</div>"""})
            st.session_state.page = "workflow"
            st.rerun()
    st.stop()



elif page == "agents":
    render_torii()
    st.markdown('<div class="sec-head">Agent Mesh — 7 Agents Active</div>', unsafe_allow_html=True)
    agents = [
        ("Alpha-7",   "#c084fc", "Data Synthesis Agent",          78,  True),
        ("Beta-3",    "#f0abfc", "Quantum Pattern Resolver",       45,  True),
        ("Gamma-9",   "#34d399", "Neural Mesh Coordinator",        92,  True),
        ("Delta-1",   "#fbbf24", "Anomaly Detection Engine",       12,  False),
        ("Epsilon-5", "#60a5fa", "Response Optimizer",             61,  True),
        ("Zeta-2",    "#fb923c", "Temporal Logic Processor",       83,  True),
        ("Eta-0",     "#a78bfa", "Distributed Consensus Layer",    55,  True),
    ]
    cols = st.columns(2)
    for idx, (name, color, role, pct, active) in enumerate(agents):
        with cols[idx % 2]:
            status_color = "#86efac" if active else "#fcd34d"
            status_label = "ACTIVE" if active else "IDLE"
            st.markdown(f"""
            <div class="agent-card" style="margin-bottom:0.9rem;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <span style="font-weight:800;color:{color};font-size:0.95rem;">{name}</span>
                <span style="background:rgba(52,211,153,0.12);color:{status_color};padding:2px 10px;border-radius:20px;font-size:0.68rem;font-family:'JetBrains Mono',monospace;">{status_label}</span>
              </div>
              <div style="color:rgba(196,166,255,0.6);font-size:0.78rem;margin-bottom:8px;">{role}</div>
              <div style="height:4px;border-radius:4px;background:rgba(255,255,255,0.06);overflow:hidden;">
                <div style="height:100%;width:{pct}%;border-radius:4px;background:{color};opacity:0.7;transition:width 1s;"></div>
              </div>
              <div style="display:flex;justify-content:space-between;margin-top:5px;font-size:0.68rem;color:rgba(196,166,255,0.4);">
                <span>Task Progress</span><span>{pct}%</span>
              </div>
            </div>""", unsafe_allow_html=True)



elif page == "workflow":
    render_torii()
    st.markdown("""
    <div style="margin-bottom:1rem;">
      <div style="font-size:1.7rem;font-weight:900;letter-spacing:-0.04em;
                  background:linear-gradient(135deg,#c084fc 0%,#f0abfc 50%,#a78bfa 100%);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
        🌸 Axon· Multi - Agentic Infrastructure
      </div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.6rem;color:#334155;
                  letter-spacing:0.16em;text-transform:uppercase;margin-top:0.1rem;">
        DWSA · Quantum Routing · Agent Swarm · Brain Synthesis · Critic · SEO · Multi - Agent
      </div>
      <div style="font-family:'Noto Sans JP',sans-serif;font-size:0.63rem;
                  color:rgba(249,168,212,0.3);letter-spacing:0.25em;margin-top:0.08rem;">
        量子自律型AIシステム · 東京イノベーション
      </div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.current_task:
        st.markdown('<div style="color:#64748b;font-size:0.84rem;margin-bottom:0.9rem;">No active task. Go to Dashboard to submit a query.</div>', unsafe_allow_html=True)
        sphere_ph = st.empty()
        with sphere_ph.container(): render_quantum_sphere("idle", 0, "HOSHI · STANDBY")
        render_stages(["pending"] * 6)
        st.stop()

    task = st.session_state.current_task
    keys = st.session_state.api_keys

    if not keys:
        st.error("⚠️ [AX-KEY] No API keys configured. Add keys in the sidebar.")
        st.stop()

    st.markdown(f'<div style="background:rgba(5,2,15,0.9);border:1px solid rgba(168,85,247,0.25);border-radius:10px;padding:0.7rem 1rem;margin-bottom:0.9rem;font-size:0.84rem;color:#c4b5fd;">🌸 <b>Active Task:</b> {task}</div>', unsafe_allow_html=True)

    if st.session_state.pipeline_done and st.session_state.pipeline_data:
        d = st.session_state.pipeline_data
        st.success("✅ Pipeline complete — results loaded from session.")
        render_quantum_sphere("complete", d.get("n_agents",0), "PIPELINE · COMPLETE")
        render_stages(["done"]*6)
        seo = d.get("seo",{})
        ap = d.get("ap",0); confidence = d.get("confidence",0); verify_score = d.get("verify_score",0)
        st.markdown(f"""<div class="metric-grid">
            <div class="metric-box"><div class="metric-val">{ap}</div><div class="metric-lbl">AP Score</div></div>
            <div class="metric-box"><div class="metric-val">{seo.get('seo_score',0)}</div><div class="metric-lbl">SEO Score</div></div>
            <div class="metric-box"><div class="metric-val">{seo.get('readability_score',0)}</div><div class="metric-lbl">Readability</div></div>
            <div class="metric-box"><div class="metric-val">{seo.get('word_count',0)}</div><div class="metric-lbl">Words</div></div>
            <div class="metric-box"><div class="metric-val">{d.get('n_agents',0)}</div><div class="metric-lbl">Agents</div></div>
            <div class="metric-box"><div class="metric-val">{confidence:.0f}%</div><div class="metric-lbl">Confidence</div></div>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"**🔖 SEO Title:** {seo.get('seo_title','')}")
        st.markdown(f"**📝 Meta Description:** {seo.get('meta_description','')}")
        kw_html = '<div class="chip-wrap">'+"".join(f'<div class="chip done">{k}</div>' for k in seo.get("keywords",[]))+"</div>"
        st.markdown("**🏷️ Keywords:**"); st.markdown(kw_html, unsafe_allow_html=True)
        st.markdown("**✅ SEO-Optimised Final Content:**")
        st.markdown(f'<div style="background:rgba(5,2,15,0.9);border:1px solid rgba(168,85,247,0.15);border-radius:12px;padding:1.1rem 1.3rem;font-size:0.83rem;line-height:1.75;color:#c4b5fd;white-space:pre-wrap;word-break:break-word;">{seo.get("optimised_content","")}</div>', unsafe_allow_html=True)
        if st.button("🔄 Run New Task"):
            st.session_state.current_task = ""; st.session_state.pipeline_done = False
            st.session_state.pipeline_data = {}; st.session_state.page = "home"; st.rerun()
        st.stop()

    
    stage_states = ["pending"] * 6
    status_ph = st.empty(); sphere_ph = st.empty()
    brain = QuantumBrain(); t_start = time.time()

    try:
        
        stage_states[0] = "active"
        with status_ph.container(): render_stages(stage_states)
        with sphere_ph.container(): render_quantum_sphere("thinking", 0, "DECOMPOSING TASK")
        st.markdown('<div class="sec-head">Stage 1 · DWSA Decomposer - Divisible work sharing Agentic orchestration</div>', unsafe_allow_html=True)
        with st.spinner("DWSA agent decomposing task…"):
            subtasks = stage_dwsa(keys, task)
        stage_states[0] = "done"
        st.markdown('<div class="chip-wrap">'+"".join(f'<div class="chip">{s["title"]}</div>' for s in subtasks)+"</div>", unsafe_allow_html=True)
        with st.expander("▸ View subtask decomposition"):
            for s in subtasks:
                st.markdown(f"**{s['id']}. {s['title']}** — {s['description']}")
                st.markdown(f"`priority_weight: {s.get('priority_weight','?')}`")

        
        stage_states[1] = "active"
        with status_ph.container(): render_stages(stage_states)
        with sphere_ph.container(): render_quantum_sphere("routing", len(subtasks), "QUANTUM ROUTING")
        st.markdown('<div class="sec-head">Stage 2 · Quantum Router — Qiskit Circuit</div>', unsafe_allow_html=True)
        with st.spinner("Running Qiskit quantum circuit…"):
            ordered_ids, qmeta = stage_quantum_routing(subtasks)
        stage_states[1] = "done"
        st.markdown(f"""<div class="qc-card">
            <div class="qc-title">⚛ Qiskit Circuit — {qmeta['n_qubits']} Qubits · {qmeta['shots']} Shots</div>
            <div class="qc-row">H → Ry(priority·π) → CX entanglement chain → Measure</div>
            <div class="qc-row">Qubit scores: {" | ".join(f"Q{i}={s}" for i,s in enumerate(qmeta['qubit_scores']))}</div>
            <div class="qc-row">Order: {'  →  '.join(f'<span style="color:#34d399">ID {i}</span>' for i in ordered_ids)}</div>
        </div>""", unsafe_allow_html=True)

        id_map = {s["id"]: s for s in subtasks}

        
        stage_states[2] = "active"
        with status_ph.container(): render_stages(stage_states)
        st.markdown('<div class="sec-head">Stage 3 · Agent Swarm — Specialist Agents</div>', unsafe_allow_html=True)
        brain_ph = st.empty(); graph_ph = st.empty(); prog = st.progress(0.0, text="Spawning agents…")

        for step_i, sid in enumerate(ordered_ids):
            s = id_map.get(sid) or id_map.get(str(sid))
            if not s: continue
            agent_id = str(sid)
            with sphere_ph.container(): render_quantum_sphere("thinking", step_i+1, f"AGENT-{agent_id} ACTIVE")
            with graph_ph.container(): render_reasoning_graph(subtasks, active_idx=step_i)
            with brain_ph.container():
                st.markdown(f'<div class="brain-card"><div class="brain-title">🧠 Quantum Brain — Live Memory ({len(brain.entries)} entries)</div>{brain.render_html()}</div>', unsafe_allow_html=True)
            with st.spinner(f"⚡ Agent-{agent_id}: {s['title']}…"):
                output = spawn_agent(keys, agent_id, s, task, brain)
            st.markdown(f"""<div class="agent-card">
                <div style="display:flex;align-items:center;gap:0.55rem;margin-bottom:0.35rem;">
                    <span class="agent-badge">Agent-{agent_id}</span>
                    <span style="font-size:0.85rem;font-weight:700;color:#e9d5ff;">{s['title']}</span>
                    <span style="width:7px;height:7px;border-radius:50%;background:#34d399;box-shadow:0 0 7px #34d39988;display:inline-block;margin-left:auto;"></span>
                </div>
                <div style="font-size:0.65rem;color:#475569;font-family:'JetBrains Mono',monospace;margin-bottom:0.25rem;">
                    Pulled {len([e for e in brain.entries if e['agent_id']!=agent_id])} brain entries · importance {min(0.6+s.get('priority_weight',0.5)*0.4,1.0):.2f}
                </div>
                <div class="agent-output">{output[:700]}{'…' if len(output)>700 else ''}</div>
            </div>""", unsafe_allow_html=True)
            prog.progress((step_i+1)/len(ordered_ids), text=f"Agent {step_i+1}/{len(ordered_ids)} complete")

        stage_states[2] = "done"
        with sphere_ph.container(): render_quantum_sphere("thinking", len(subtasks), "SYNTHESISING")
        with graph_ph.container(): render_reasoning_graph(subtasks, active_idx=len(subtasks))
        with brain_ph.container():
            st.markdown(f'<div class="brain-card"><div class="brain-title">🧠 Quantum Brain — Complete ({len(brain.entries)} entries)</div>{brain.render_html()}</div>', unsafe_allow_html=True)

        
        stage_states[3] = "active"
        with status_ph.container(): render_stages(stage_states)
        st.markdown('<div class="sec-head">Stage 4 · Brain Synthesis</div>', unsafe_allow_html=True)
        with st.spinner("Synthesiser reading complete memory…"):
            synthesised = stage_synthesis(keys, task, brain)
        stage_states[3] = "done"
        st.markdown("**Synthesised Output:**")
        st.markdown(f'<div style="background:rgba(5,2,15,0.9);border:1px solid rgba(168,85,247,0.15);border-radius:12px;padding:1.1rem 1.3rem;font-size:0.83rem;line-height:1.75;color:#c4b5fd;white-space:pre-wrap;word-break:break-word;">{synthesised}</div>', unsafe_allow_html=True)

        
        stage_states[4] = "active"
        with status_ph.container(): render_stages(stage_states)
        with sphere_ph.container(): render_quantum_sphere("verifying", len(subtasks), "SELF-AUDITING")
        st.markdown('<div class="sec-head">Stage 5 · Self-Critic Agent</div>', unsafe_allow_html=True)
        with st.spinner("Critic agent reviewing synthesis…"):
            critic = stage_critic(keys, task, synthesised, brain)
        crit_html = ""
        for item in critic.get("contradictions",[])[:3]:
            crit_html += f'<div style="color:#f87171;font-size:0.74rem;margin:0.16rem 0;">⚠ {item}</div>'
        for item in critic.get("weak_reasoning",[])[:3]:
            crit_html += f'<div style="color:#fbbf24;font-size:0.74rem;margin:0.16rem 0;">△ {item}</div>'
        verdict_color = "#34d399" if critic.get("verdict")=="PASS" else "#fbbf24" if critic.get("verdict")=="REVISE" else "#f87171"
        st.markdown(f"""<div class="critic-card">
          <div class="critic-title">🔍 Critic Agent Report</div>
          <div style="display:flex;align-items:center;gap:0.9rem;margin-bottom:0.45rem">
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;font-weight:700;color:{verdict_color}">{critic.get('verdict','?')}</div>
            <div style="font-size:0.72rem;color:#475569">Score: <b style="color:{verdict_color}">{critic.get('critic_score',0)}/100</b></div>
          </div>
          {crit_html if crit_html else '<div style="color:#34d399;font-size:0.75rem;">✓ No major issues detected.</div>'}
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="sec-head">Stage 5b · Verification Agent</div>', unsafe_allow_html=True)
        with st.spinner("Verifier agent checking consistency…"):
            verifier = stage_verifier(keys, task, synthesised, critic, brain)
        verify_score = verifier.get("verification_score", 70)
        v_color = "#34d399" if verifier.get("final_verdict")=="VERIFIED" else "#fbbf24"
        strengths_html = "".join(f'<div style="color:#34d399;font-size:0.74rem;margin:0.15rem 0;">✓ {s}</div>' for s in verifier.get("strengths",[])[:3])
        v_issues_html  = "".join(f'<div style="color:#fbbf24;font-size:0.74rem;margin:0.15rem 0;">△ {s}</div>' for s in verifier.get("issues",[])[:3])
        st.markdown(f"""<div class="verifier-card">
          <div class="verifier-title">✅ Verification Report</div>
          <div style="display:flex;align-items:center;gap:0.9rem;margin-bottom:0.45rem">
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.9rem;font-weight:700;color:{v_color}">{verifier.get('final_verdict','?')}</div>
            <div style="font-size:0.7rem;color:#475569">
              Consistency: <b style="color:{v_color}">{verifier.get('consistency_check','?')}</b> &nbsp;·&nbsp;
              Completeness: <b style="color:{v_color}">{verifier.get('completeness_score',0)}/100</b> &nbsp;·&nbsp;
              Score: <b style="color:{v_color}">{verify_score}/100</b>
            </div>
          </div>
          {strengths_html}{v_issues_html}
        </div>""", unsafe_allow_html=True)

        with graph_ph.container(): render_reasoning_graph(subtasks, active_idx=len(subtasks), critic_done=True, verifier_done=True)
        stage_states[4] = "done"

        confidence = compute_confidence(critic, verifier, brain, len(subtasks))
        st.markdown(f"""<div class="confidence-wrap">
          <div style="font-size:0.76rem;color:#94a3b8;margin-bottom:0.25rem;">Confidence Engine</div>
          <div class="confidence-bar-bg"><div class="confidence-bar-fill" style="width:{confidence}%"></div></div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:0.88rem;font-weight:700;
                      background:linear-gradient(135deg,#c084fc,#a78bfa);-webkit-background-clip:text;
                      -webkit-text-fill-color:transparent;">{confidence:.1f}% confidence</div>
        </div>""", unsafe_allow_html=True)

        # Stage 6 — SEO
        stage_states[5] = "active"
        with status_ph.container(): render_stages(stage_states)
        with sphere_ph.container(): render_quantum_sphere("complete", len(subtasks), "SEO OPTIMISING")
        st.markdown('<div class="sec-head">Stage 6 · SEO Agent — Optimising & Scoring</div>', unsafe_allow_html=True)
        with st.spinner("SEO agent processing…"):
            seo = stage_seo(keys, synthesised, task)
        stage_states[5] = "done"
        with status_ph.container(): render_stages(stage_states)

        t_end = time.time()
        exec_time = round(t_end - t_start, 1)
        with sphere_ph.container(): render_quantum_sphere("complete", len(subtasks), "PIPELINE COMPLETE")
        with graph_ph.container(): render_reasoning_graph(subtasks, active_idx=len(subtasks), critic_done=True, verifier_done=True, synthesis_done=True)

        rs = seo.get("readability_score", 75) / 100
        ap = compute_ap(rs, seo.get("seo_score", 80), len(subtasks))

        st.markdown('<div class="sec-head">⚛ Final Returns — Σ|Ψ⟩(DWSA) = AP</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="metric-grid">
            <div class="metric-box"><div class="metric-val">{ap}</div><div class="metric-lbl">AP Score</div></div>
            <div class="metric-box"><div class="metric-val">{seo.get('seo_score',0)}</div><div class="metric-lbl">SEO Score</div></div>
            <div class="metric-box"><div class="metric-val">{seo.get('readability_score',0)}</div><div class="metric-lbl">Readability</div></div>
            <div class="metric-box"><div class="metric-val">{seo.get('word_count',0)}</div><div class="metric-lbl">Words</div></div>
            <div class="metric-box"><div class="metric-val">{len(subtasks)}</div><div class="metric-lbl">Agents</div></div>
            <div class="metric-box"><div class="metric-val">{len(brain.entries)}</div><div class="metric-lbl">Brain Entries</div></div>
            <div class="metric-box"><div class="metric-val">{critic.get('critic_score',0)}</div><div class="metric-lbl">Critic</div></div>
            <div class="metric-box"><div class="metric-val">{verify_score}</div><div class="metric-lbl">Verify</div></div>
            <div class="metric-box"><div class="metric-val">{exec_time}s</div><div class="metric-lbl">Exec Time</div></div>
            <div class="metric-box"><div class="metric-val">{confidence:.0f}%</div><div class="metric-lbl">Confidence</div></div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"**🔖 SEO Title:** {seo.get('seo_title','')}")
        st.markdown(f"**📝 Meta Description:** {seo.get('meta_description','')}")
        kw_html = '<div class="chip-wrap">'+"".join(f'<div class="chip done">{k}</div>' for k in seo.get("keywords",[]))+"</div>"
        st.markdown("**🏷️ Keywords:**"); st.markdown(kw_html, unsafe_allow_html=True)
        st.markdown("**✅ SEO-Optimised Final Content:**")
        st.markdown(f'<div style="background:rgba(5,2,15,0.9);border:1px solid rgba(168,85,247,0.15);border-radius:12px;padding:1.1rem 1.3rem;font-size:0.83rem;line-height:1.75;color:#c4b5fd;white-space:pre-wrap;word-break:break-word;">{seo.get("optimised_content","")}</div>', unsafe_allow_html=True)

        st.success(f"✅ Pipeline complete · {len(subtasks)} agents · AP = {ap} · Confidence = {confidence:.0f}% · {exec_time}s")

        st.session_state.pipeline_done = True
        st.session_state.pipeline_data = {"seo":seo,"ap":ap,"confidence":confidence,
            "verify_score":verify_score,"n_agents":len(subtasks)}
        st.session_state.chat_history.append({"role":"axon",
            "content":f"✅ Pipeline complete! AP Score: <b style='color:#c084fc'>{ap}</b> · Confidence: <b style='color:#a78bfa'>{confidence:.0f}%</b> · {len(subtasks)} agents · {exec_time}s"})

        if st.button("← Back to Dashboard", key="back_home_btn"):
            st.session_state.page = "home"; st.rerun()

    except RuntimeError as e:
        st.error(f"[AX-KEY] {e}")
    except (json.JSONDecodeError, ValueError) as e:
        st.error(f"[AX-JSON] JSON parsing error: {e}")
    except Exception as e:
        code = classify_error(e)
        st.error(f"[{code}] Pipeline error: {e}")
        with st.expander("Full traceback"):
            import traceback; st.code(traceback.format_exc())



elif page == "builder":
    render_torii()
    st.markdown('<div class="sec-head">Builder Info</div>', unsafe_allow_html=True)
    skills_html = "".join(f'<span class="skill-chip">{sk}</span>' for sk in BUILDER["skills"])
    st.markdown(f"""
    <div class="builder-card">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.4rem;">
        <div style="display:flex;align-items:center;gap:1.2rem;">
          <div class="builder-avatar">{BUILDER["initials"]}</div>
          <div>
            <div class="builder-name">{BUILDER["name"]}</div>
            <div class="builder-role">{BUILDER["role"]}</div>
          </div>
        </div>
        <div class="locked-badge">🔒 Profile Locked</div>
      </div>
      <div style="background:rgba(251,191,36,0.06);border:1px solid rgba(251,191,36,0.15);
                  border-radius:10px;padding:0.65rem 1rem;margin-bottom:1.3rem;
                  font-size:0.75rem;color:rgba(251,191,36,0.7);font-family:'JetBrains Mono',monospace;">
        ⚠ This profile is managed by the system administrator and cannot be edited.
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.3rem;">
        <div>
          <div class="builder-field-label">Email</div>
          <div class="builder-field-val">{BUILDER["email"]}</div>
        </div>
        <div>
          <div class="builder-field-label">Location</div>
          <div class="builder-field-val">{BUILDER["location"]}</div>
        </div>
      </div>
      <div style="margin-bottom:1.3rem;">
        <div class="builder-field-label">Bio</div>
        <div style="font-size:0.82rem;color:#c4b5fd;line-height:1.7;margin-top:0.2rem;">{BUILDER["bio"]}</div>
      </div>
      <div>
        <div class="builder-field-label">Specialisations</div>
        <div style="margin-top:0.4rem;">{skills_html}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)



elif page == "help":
    render_torii()
    st.markdown('<div class="sec-head">Customer Help</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#64748b;font-size:0.82rem;margin-bottom:1rem;">Ask anything about the Hoshi system, DWSA, Quantum Layer, or spawned agents.</div>', unsafe_allow_html=True)

    if "help_history" not in st.session_state:
        st.session_state.help_history = []

    
    if not st.session_state.help_history:
        st.markdown("""<div class="chat-bubble-axon" style="max-width:700px;">
          <div class="axon-avatar">HOSHI SUPPORT</div>
          Hello! I'm Hoshi's support assistant. Ask me anything about the DWSA system, quantum layer, spawned agents, or anything else. 🌸
        </div>""", unsafe_allow_html=True)

    for msg in st.session_state.help_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-axon" style="max-width:700px;"><div class="axon-avatar">HOSHI SUPPORT</div>{msg["content"]}</div>', unsafe_allow_html=True)

    
    faq_cols = st.columns(4)
    faqs = ["How do I spawn an agent?", "What is DWSA?", "How does quantum routing work?", "Check system status"]
    for i, (col, faq) in enumerate(zip(faq_cols, faqs)):
        with col:
            if st.button(faq, key=f"faq_{i}", use_container_width=True):
                if not st.session_state.api_keys:
                    st.session_state.help_history.append({"role":"user","content":faq})
                    st.session_state.help_history.append({"role":"assistant","content":"Please configure your API keys in the sidebar to use the live AI support."})
                    st.rerun()
                else:
                    st.session_state.help_history.append({"role":"user","content":faq})
                    keys = st.session_state.api_keys
                    system = "You are Hoshi AI Support — a helpful assistant for the Hoshi AI Command Center. The system features DWSA (Distributed Wave State Architecture), a Quantum Layer powered by Qiskit, and Spawned Agents. Answer user questions warmly and concisely in 2-4 sentences."
                    with st.spinner("Thinking…"):
                        answer = gemini_text(keys, faq, system)
                    st.session_state.help_history.append({"role":"assistant","content":answer})
                    st.rerun()

    col_inp, col_btn = st.columns([5, 1])
    with col_inp:
        help_input = st.text_input("Ask a question", placeholder="Ask about DWSA, agents, quantum layer…",
                                   label_visibility="collapsed", key="help_input")
    with col_btn:
        help_send = st.button("Send", use_container_width=True, key="help_send")

    if help_send and help_input.strip():
        question = help_input.strip()
        st.session_state.help_history.append({"role":"user","content":question})
        if not st.session_state.api_keys:
            fallback = {"spawn":"Navigate to Agent Mesh and the DWSA system will spawn agents automatically when you run a task.",
                        "dwsa":"DWSA (Distributed Wave State Architecture) decomposes your task into 4–6 atomic subtasks and routes them via quantum circuits.",
                        "quantum":"The Quantum Layer uses Qiskit circuits to determine optimal agent execution order based on priority weights.",
                        "status":"Check the sidebar for live System Status — DWSA Core, Quantum Layer, and active agent count."}
            low = question.lower()
            ans = next((v for k,v in fallback.items() if k in low), "That's a great question! Check the Quantum Workflow page for full pipeline details.")
        else:
            keys = st.session_state.api_keys
            system = "You are Hoshi AI Support — a helpful assistant for the Hoshi AI Command Center. The system features DWSA (Distributed Wave State Architecture), a Quantum Layer powered by Qiskit, and Spawned Agents. Answer user questions warmly and concisely in 2-4 sentences."
            history_prompt = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in st.session_state.help_history[-6:])
            with st.spinner("Thinking…"):
                ans = gemini_text(keys, history_prompt, system)
        st.session_state.help_history.append({"role":"assistant","content":ans})
        st.rerun()



elif page == "settings":
    render_torii()
    st.markdown('<div class="sec-head">Settings</div>', unsafe_allow_html=True)
    st.markdown('<div style="max-width:680px;">', unsafe_allow_html=True)

    with st.expander("🌸 Visual & Theme", expanded=True):
        st.markdown('<div style="font-size:0.8rem;color:#a78bfa;margin-bottom:0.5rem;">Hoshi uses a purple-sakura aesthetic themed around the Hoshi quantum identity. Visual settings are managed via the system profile.</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Sphere Palette", ["Deep Purple Nebula","Cosmic Rainbow","Cyberpunk Cyan","Solar Flare & Gold"], key="s_palette")
        with c2:
            st.slider("Glow Intensity", 0.5, 6.0, 3.0, 0.5, key="s_glow")
        st.slider("Rotation Speed", 0.0, 3.0, 1.0, 0.1, key="s_rot")

    with st.expander("⚛ Pipeline Settings", expanded=False):
        st.markdown('<div style="font-size:0.8rem;color:#a78bfa;margin-bottom:0.5rem;">Configure the Hoshi quantum pipeline behaviour.</div>', unsafe_allow_html=True)
        st.slider("Max subtasks (DWSA)", 4, 6, 5, key="s_subtasks")
        st.slider("Agent temperature", 0.1, 1.0, 0.7, 0.05, key="s_temp")

    with st.expander("🔐 Profile & Security", expanded=False):
        st.markdown("""<div style="background:rgba(251,191,36,0.06);border:1px solid rgba(251,191,36,0.15);
                    border-radius:10px;padding:0.75rem 1rem;font-size:0.78rem;
                    color:rgba(251,191,36,0.8);font-family:'JetBrains Mono',monospace;">
            🔒 The builder profile is locked and managed by the system administrator.<br>
            Profile editing has been disabled. Contact the admin to request changes.
        </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
