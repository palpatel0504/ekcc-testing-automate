import streamlit as st
import subprocess
import os
import time
import select
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
STATE_DIRS = {
    "Haryana": BASE_DIR / "Haryana",
    "Gujarat":  BASE_DIR / "gujarat",
    "Punjab":   BASE_DIR / "Punjab",
    "Bihar":    BASE_DIR / "Bihar",
}
STATE_ALIASES = {
    "Haryana(RRB)": "Haryana",
    "Gujarat(DCCB)": "Gujarat",
    "Punjab(RRB)":  "Punjab",
    "Bihar(RRB)":   "Bihar",
}
# VENV_PYTEST = BASE_DIR / "venv" / "bin" / "pytest"
VENV_PYTEST = "pytest"
VENV_PYTHON = "python"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Automation Monitor", layout="wide", initial_sidebar_state="collapsed")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600&family=Syne:wght@400;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"] {
    background: #090c10 !important;
    color: #c9d1d9 !important;
    font-family: 'Syne', sans-serif !important;
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 80% 40% at 70% -10%, rgba(31,111,235,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 50% 30% at 10% 90%, rgba(16,185,129,0.06) 0%, transparent 55%),
        #090c10 !important;
}
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="collapsedControl"] { display: none !important; }
.block-container { padding: 1.8rem 2.2rem 2rem !important; max-width: 100% !important; }
h1,h2,h3,h4,h5,h6,
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3,.stMarkdown h4 {
    font-family: 'Syne', sans-serif !important;
    letter-spacing: -0.02em !important;
}
.app-header {
    display:flex; align-items:center; gap:16px;
    padding:0 0 1.4rem 0;
    border-bottom:1px solid rgba(31,111,235,0.25);
    margin-bottom:1.6rem;
}
.app-header .icon {
    width:42px; height:42px;
    background:linear-gradient(135deg,#1f6feb,#10b981);
    border-radius:10px; display:flex; align-items:center;
    justify-content:center; font-size:20px; flex-shrink:0;
}
.app-header .title-block h1 {
    margin:0 !important; padding:0 !important;
    font-size:1.55rem !important; font-weight:800 !important;
    color:#f0f6fc !important; letter-spacing:-0.03em !important; line-height:1.1 !important;
}
.app-header .title-block p {
    margin:2px 0 0 0 !important; font-size:0.78rem !important;
    color:#6e7681 !important; font-family:'JetBrains Mono',monospace !important;
    letter-spacing:0.04em !important;
}
.status-pill {
    margin-left:auto; display:flex; align-items:center; gap:8px;
    padding:6px 14px; border-radius:100px;
    font-family:'JetBrains Mono',monospace; font-size:0.72rem;
    font-weight:500; letter-spacing:0.08em; text-transform:uppercase;
}
.status-pill.idle    { background:rgba(110,118,129,0.15); border:1px solid rgba(110,118,129,0.3); color:#8b949e; }
.status-pill.running { background:rgba(16,185,129,0.12);  border:1px solid rgba(16,185,129,0.35); color:#10b981; }
.status-pill .dot { width:7px; height:7px; border-radius:50%; }
.status-pill.idle .dot    { background:#6e7681; }
.status-pill.running .dot { background:#10b981; box-shadow:0 0 6px #10b981; animation:pulse 1.4s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.85)} }
.panel { background:rgba(13,17,23,.85); border:1px solid rgba(31,111,235,.18); border-radius:12px; padding:1.2rem 1.3rem; backdrop-filter:blur(8px); margin-bottom:1rem; }
.panel-title {
    font-size:0.7rem !important; font-weight:600 !important; letter-spacing:0.12em !important;
    text-transform:uppercase !important; color:#6e7681 !important; margin:0 0 1rem 0 !important;
    display:flex; align-items:center; gap:8px;
}
.panel-title::before { content:''; display:block; width:14px; height:2px; background:linear-gradient(90deg,#1f6feb,#10b981); border-radius:2px; }
[data-testid="stSelectbox"] label { font-family:'JetBrains Mono',monospace !important; font-size:0.7rem !important; color:#6e7681 !important; letter-spacing:0.1em !important; text-transform:uppercase !important; }
[data-testid="stSelectbox"] > div > div { background:rgba(22,27,34,.9) !important; border:1px solid rgba(31,111,235,.25) !important; border-radius:8px !important; color:#c9d1d9 !important; font-family:'JetBrains Mono',monospace !important; font-size:0.85rem !important; transition:border-color .2s; }
[data-testid="stSelectbox"] > div > div:hover { border-color:rgba(31,111,235,.55) !important; }
[data-testid="stCheckbox"] label { font-family:'JetBrains Mono',monospace !important; font-size:0.8rem !important; color:#8b949e !important; }
[data-testid="stCheckbox"] span[data-testid="stCheckboxCheck"] { background:#1f6feb !important; border-color:#1f6feb !important; border-radius:4px !important; }
[data-testid="stButton"] > button { font-family:'JetBrains Mono',monospace !important; font-size:0.78rem !important; font-weight:600 !important; letter-spacing:0.08em !important; text-transform:uppercase !important; border-radius:8px !important; padding:0.52rem 1rem !important; border:none !important; transition:all .18s ease !important; width:100% !important; }
[data-testid="stButton"] > button[kind="primary"]          { background:linear-gradient(135deg,#1f6feb 0%,#1158c7 100%) !important; color:#fff !important; box-shadow:0 4px 18px rgba(31,111,235,.28) !important; }
[data-testid="stButton"] > button[kind="primary"]:hover:not(:disabled)    { box-shadow:0 6px 24px rgba(31,111,235,.45) !important; transform:translateY(-1px) !important; }
[data-testid="stButton"] > button[kind="secondary"]        { background:rgba(248,81,73,.1) !important; color:#f85149 !important; border:1px solid rgba(248,81,73,.3) !important; }
[data-testid="stButton"] > button[kind="secondary"]:hover:not(:disabled)  { background:rgba(248,81,73,.18) !important; border-color:rgba(248,81,73,.55) !important; transform:translateY(-1px) !important; }
[data-testid="stButton"] > button:disabled { opacity:.35 !important; cursor:not-allowed !important; transform:none !important; }
[data-testid="stMarkdownContainer"] h3 { font-size:0.72rem !important; font-weight:600 !important; color:#6e7681 !important; text-transform:uppercase !important; letter-spacing:0.12em !important; margin:1.4rem 0 .8rem 0 !important; display:flex; align-items:center; gap:8px; }
[data-testid="stCode"] { border-radius:10px !important; border:1px solid rgba(31,111,235,.15) !important; background:#0d1117 !important; }
[data-testid="stCode"] code, pre { font-family:'JetBrains Mono',monospace !important; font-size:0.74rem !important; line-height:1.65 !important; color:#8b949e !important; }
[data-testid="stTable"] table { background:transparent !important; border-collapse:collapse !important; width:100% !important; font-family:'JetBrains Mono',monospace !important; font-size:0.76rem !important; }
[data-testid="stTable"] th { background:rgba(31,111,235,.08) !important; color:#6e7681 !important; font-size:0.65rem !important; letter-spacing:0.1em !important; text-transform:uppercase !important; padding:7px 12px !important; border-bottom:1px solid rgba(31,111,235,.2) !important; font-weight:600 !important; }
[data-testid="stTable"] td { color:#c9d1d9 !important; padding:6px 12px !important; border-bottom:1px solid rgba(255,255,255,.04) !important; vertical-align:middle !important; }
[data-testid="stTable"] tr:last-child td { border-bottom:none !important; }
[data-testid="stTable"] td:first-child { color:#8b949e !important; font-weight:500 !important; }
[data-testid="stTable"] td:last-child  { color:#10b981 !important; }
[data-testid="stMarkdownContainer"] h4 { font-family:'Syne',sans-serif !important; font-size:0.78rem !important; font-weight:700 !important; color:#f0f6fc !important; letter-spacing:0.01em !important; margin:1rem 0 .4rem 0 !important; padding-left:10px !important; border-left:2px solid #1f6feb !important; }
[data-testid="stAlert"] { background:rgba(31,111,235,.06) !important; border:1px solid rgba(31,111,235,.2) !important; border-radius:8px !important; font-family:'JetBrains Mono',monospace !important; font-size:0.78rem !important; color:#8b949e !important; }
[data-testid="stToast"] { background:rgba(16,185,129,.12) !important; border:1px solid rgba(16,185,129,.3) !important; border-radius:10px !important; color:#10b981 !important; font-family:'JetBrains Mono',monospace !important; font-size:0.8rem !important; }
[data-testid="stImage"] img { border-radius:8px !important; border:1px solid rgba(31,111,235,.2) !important; }
[data-testid="stImage"] p  { font-family:'JetBrains Mono',monospace !important; font-size:0.68rem !important; color:#6e7681 !important; margin-top:4px !important; }
hr { border-color:rgba(31,111,235,.15) !important; margin:1rem 0 !important; }
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:rgba(31,111,235,.35); border-radius:10px; }
::-webkit-scrollbar-thumb:hover { background:rgba(31,111,235,.6); }
[data-testid="stHorizontalBlock"] > div { padding:0 .5rem !important; }
[data-testid="stHorizontalBlock"] > div:first-child { padding-left:0 !important; }
[data-testid="stHorizontalBlock"] > div:last-child  { padding-right:0 !important; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def normalize_state(name: str | None) -> str:
    name = STATE_ALIASES.get(name, name) if name else None
    return name if name in STATE_DIRS else next(iter(STATE_DIRS))


# State-specific schema definitions
_LAND_FIELDS = {
    "Punjab": {"district": "-", "subdistrict": "-", "village": "-",
               "hadbast no": "-", "khewat no": "-", "khatoni no": "-", "khasara no": "-",
               "land size": "-", "irrigation": "-", "market value": "-"},
    "Haryana": {"district": "-", "subdistrict": "-", "village": "-",
                "survey number": "-", "land size": "-", "irrigation": "-", "market value": "-"},
    "Gujarat":  {"district": "-", "subdistrict": "-", "village": "-",
                 "survey number": "-", "land size": "-", "irrigation": "-", "market value": "-"},
    "Bihar":    {"district": "-", "subdistrict": "-", "village": "-",
                 "khata no": "-", "khasra no": "-",
                 "land size": "-", "irrigation": "-", "market value": "-"},
}
_CROP_FIELDS = {
    "Punjab":  {"crop name": "-", "size of cultivation": "-"},
    "Haryana": {"survey number": "-", "crop name": "-", "size of cultivation": "-"},
    "Gujarat": {"survey number": "-", "crop name": "-", "size of cultivation": "-"},
    "Bihar":   {"crop name": "-", "size of cultivation": "-"},
}
_USER_FIELDS = {"name": "pal r patel", "bank type": "-", "pacs or branch": "-", "bank name": "-", "branch": "-"}


def reset_extracted_data(state: str | None = None):
    state = state or st.session_state.get("selected_state", "Gujarat")
    # Fallback to a generic schema if the state isn't explicitly defined
    land_fields  = _LAND_FIELDS.get(state,  {"district": "-", "subdistrict": "-", "village": "-", "land size": "-", "irrigation": "-", "market value": "-"})
    crop_fields  = _CROP_FIELDS.get(state,  {"crop name": "-", "size of cultivation": "-"})
    st.session_state.data_extracted = {
        "User Details": _USER_FIELDS.copy(),
        "Land Details": land_fields.copy(),
        "Crop Details": crop_fields.copy(),
    }


# ── Session state init ────────────────────────────────────────────────────────
ss = st.session_state
for k, v in [("running", False), ("logs", []), ("process", None), ("run_headed_mode", True)]:
    ss.setdefault(k, v)

ss.selected_state = normalize_state(ss.get("selected_state"))
ss.run_state      = normalize_state(ss.get("run_state", ss.selected_state))

if "data_extracted" not in ss:
    reset_extracted_data(ss.selected_state)
if "_last_data_state" not in ss:
    ss._last_data_state = ss.selected_state


# ── Process management ────────────────────────────────────────────────────────
def start_test_run(state: str, headed: bool):
    cmd = [str(VENV_PYTEST), "-s"] + (["--headed"] if headed else []) + ["--browser", "chromium", "test_smoke.py"]
    env = {**os.environ, "PATH": f"{BASE_DIR}/venv/bin:{os.environ.get('PATH', '')}"}
    proc = subprocess.Popen(cmd, cwd=str(STATE_DIRS[state]),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, env=env)
    os.set_blocking(proc.stdout.fileno(), False)
    ss.process, ss.running, ss.run_state, ss.run_headed_mode = proc, True, state, headed


def stop_test_run():
    proc = ss.process
    if proc is None:
        return
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    if proc.stdout:
        proc.stdout.close()
    ss.process, ss.running = None, False
    ss.logs.append("[app] Test stopped by user.")


def read_process_output():
    proc = ss.process
    if proc is None or proc.stdout is None:
        return

    def _after(keyword: str, line: str, raw: str) -> str:
        idx = line.find(keyword.lower())
        return raw[idx + len(keyword):].strip().rstrip(".") if idx != -1 else ""

    while True:
        if not select.select([proc.stdout], [], [], 0)[0]:
            break
        raw = proc.stdout.readline()
        if not raw:
            break
        line = raw.strip()
        if not line:
            continue
        ss.logs.append(line)
        ll = line.lower()
        d  = ss.data_extracted
        rs = ss.run_state

        if   "selecting bank type:"  in ll: d["User Details"]["bank type"]     = _after("bank type:",  ll, line)
        elif "selecting bank name:"  in ll: d["User Details"]["bank name"]      = _after("bank name:",  ll, line)
        elif "selecting branch:"     in ll: d["User Details"]["branch"]         = _after("branch:",     ll, line)
        elif "selecting branch for"  in ll and "where to apply" in ll:
                                            d["User Details"]["pacs or branch"] = "Branch"
        elif "entering survey number:" in ll:
            val = _after("survey number:", ll, line)
            for section in ("Land Details", "Crop Details"):
                if "survey number" in d.get(section, {}):
                    d[section]["survey number"] = val
        elif "filling land details form" in ll or "filling punjab land details form" in ll:
            d["Land Details"].update({"land size": "Randomly selected (3-7)", "irrigation": "Randomly selected", "market value": "3456"})
        elif "selected crop name" in ll:
            val = _after("crop name:", ll, line)
            d["Crop Details"]["crop name"] = val or ("Other Pulse Crops" if rs == "Gujarat" else "-")
        elif "entered cultivation size:" in ll:
            d["Crop Details"]["size of cultivation"] = _after("cultivation size:", ll, line)
        elif "selecting district:"    in ll: d["Land Details"]["district"]    = _after("selecting district:",    ll, line)
        elif "selected district:"     in ll: d["Land Details"]["district"]    = _after("selected district:",     ll, line)
        elif "selecting sub-district:" in ll: d["Land Details"]["subdistrict"] = _after("selecting sub-district:", ll, line)
        elif "selected sub-district:"  in ll: d["Land Details"]["subdistrict"] = _after("selected sub-district:",  ll, line)
        elif "selecting subdistrict:"  in ll: d["Land Details"]["subdistrict"] = _after("selecting subdistrict:",  ll, line)
        elif "selecting village:"      in ll: d["Land Details"]["village"]     = _after("selecting village:",      ll, line)
        elif "selected village:"       in ll: d["Land Details"]["village"]     = _after("selected village:",       ll, line)
        elif rs == "Gujarat" and "selecting" in ll:
            if   "vadodara" in ll: d["Land Details"]["district"]    = "Vadodara"
            elif "savli"    in ll: d["Land Details"]["subdistrict"] = "Savli"
            elif "ajabpura" in ll: d["Land Details"]["village"]     = "Ajabpura"
        elif rs == "Punjab":
            for field in ("hadbast no", "khewat no", "khatoni no", "khasara no"):
                if f"{field} filled:" in ll and field in d["Land Details"]:
                    d["Land Details"][field] = _after(f"{field} filled:", ll, line)
        elif rs == "Bihar" and "filling bihar land" in ll:
            # Log: "Filling Bihar land → Khata: 123, Khasra: 45"
            import re as _re
            m = _re.search(r"khata:\s*(\S+),?\s*khasra:\s*(\S+)", ll)
            if m:
                d["Land Details"]["khata no"]  = m.group(1).rstrip(",")
                d["Land Details"]["khasra no"] = m.group(2).rstrip(".")


# ── App Header ────────────────────────────────────────────────────────────────
status_class = "running" if ss.running else "idle"
st.markdown(f"""
<div class="app-header">
  <div class="icon">⚙️</div>
  <div class="title-block">
    <h1>Automation Monitor</h1>
    <p>Farmer Loan Automation · Playwright + pytest</p>
  </div>
  <div class="status-pill {status_class}">
    <span class="dot"></span>
    {"Running" if ss.running else "Idle"}
  </div>
</div>
""", unsafe_allow_html=True)

active_state = ss.run_state if ss.running else ss.selected_state
col_ctrl, col_logs, col_data = st.columns([1, 2.2, 1.4])

# ── Controls ──────────────────────────────────────────────────────────────────
with col_ctrl:
    st.markdown('<p class="panel-title">Controls</p>', unsafe_allow_html=True)

    selected_state = st.selectbox("State", list(STATE_DIRS), index=list(STATE_DIRS).index(ss.selected_state), disabled=ss.running)
    ss.selected_state = selected_state

    if not ss.running and selected_state != ss._last_data_state:
        ss._last_data_state = selected_state
        reset_extracted_data(selected_state)
        st.rerun()

    headed_mode = st.checkbox("Show Browser (Headed)", value=True, disabled=ss.running)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    if st.button("▶  Start Test", disabled=ss.running, use_container_width=True, type="primary"):
        ss.logs = []
        reset_extracted_data(selected_state)
        start_test_run(selected_state, headed_mode)
        st.toast("Test started!", icon="🚀")
        st.rerun()

    if st.button("■  Stop Test", disabled=not ss.running, use_container_width=True):
        stop_test_run()
        st.rerun()

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown('<p class="panel-title">Info</p>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:rgba(31,111,235,.06);border:1px solid rgba(31,111,235,.18);border-radius:10px;
                padding:12px 14px;font-family:'JetBrains Mono',monospace;font-size:.75rem;line-height:2;color:#8b949e;">
        <span style="color:#6e7681">State &nbsp;&nbsp;&nbsp;&nbsp;</span><span style="color:#c9d1d9;float:right">{active_state}</span><br>
        <span style="color:#6e7681">Mode &nbsp;&nbsp;&nbsp;&nbsp;</span><span style="color:#c9d1d9;float:right">{"Headed" if ss.run_headed_mode else "Headless"}</span><br>
        <span style="color:#6e7681">Log lines</span><span style="color:#10b981;float:right">{len(ss.logs)}</span>
    </div>""", unsafe_allow_html=True)

# ── Live Logs ─────────────────────────────────────────────────────────────────
with col_logs:
    st.markdown('<p class="panel-title">Live Logs</p>', unsafe_allow_html=True)
    log_container = st.empty()

    def render_logs():
        log_container.code(
            "\n".join(ss.logs) if ss.logs else "// No logs yet — start a test to see output here...",
            language="log",
        )

    if ss.running:
        
        if ss.process is None:
            ss.running = False
            st.rerun()

        read_process_output()
        render_logs()

        if ss.process.poll() is None:
            time.sleep(1)
            st.rerun()
        else:
            read_process_output()          # flush remaining output
            if ss.process.stdout:
                ss.process.stdout.close()
            ss.process, ss.running = None, False
            st.rerun()
    else:
        render_logs()

# ── Data & Artifacts ──────────────────────────────────────────────────────────
with col_data:
    st.markdown('<p class="panel-title">Test Data</p>', unsafe_allow_html=True)
    artifacts_dir = STATE_DIRS[active_state] / "artifacts" / "error-screenshots"

    table_container = st.empty()
    with table_container.container():
        for section, fields in ss.data_extracted.items():
            st.markdown(f"#### {section}")
            st.table([{"Field": k.title(), "Value": v} for k, v in fields.items()])

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    st.markdown('<p class="panel-title">Screenshots</p>', unsafe_allow_html=True)

    if artifacts_dir.exists():
        images = sorted(artifacts_dir.glob("*.png"), key=os.path.getmtime, reverse=True)[:5]
        if images:
            for img in images:
                st.image(str(img), caption=img.name, use_container_width=True)
        else:
            st.info("No screenshots captured yet.")
    else:
        st.info("Artifacts folder not created yet.")