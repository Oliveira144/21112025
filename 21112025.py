# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ========== CONFIG ==========
st.set_page_config(page_title="Football Studio Analyzer - Valor + Padrão", layout="wide")
st.title("Football Studio Analyzer — Valor + Padrão (Profissional)")

# ========== CONSTANTS ==========
CARD_MAP = {"A":14, "K":13, "Q":12, "J":11, "10":10, "9":9, "8":8, "7":7, "6":6, "5":5, "4":4, "3":3, "2":2}
HIGH = {"A","K","Q","J"}
MEDIUM = {"10","9","8"}
LOW = {"7","6","5","4","3","2"}
CARD_STRENGTH = {"A":5,"K":5,"Q":5,"J":4,"10":4,"9":3,"8":3,"7":2,"6":1,"5":1,"4":1,"3":1,"2":1}
CARD_ORDER = ["A","K","Q","J","10","9","8","7","6","5","4","3","2"]

DEFAULT_BREAK_THRESHOLD = 50  # percent
MAX_COLS = 9
MAX_LINES = 10

# ========== HELPERS ==========
def normalize_card_label(label: str) -> str:
    return str(label).strip().upper()

def card_value(label: str) -> int:
    return CARD_MAP.get(normalize_card_label(label), 0)

def card_class(label: str) -> str:
    lab = normalize_card_label(label)
    if lab in HIGH:
        return "alta"
    if lab in MEDIUM:
        return "media"
    if lab in LOW:
        return "baixa"
    return "tie"

def card_strength(label: str) -> int:
    return CARD_STRENGTH.get(normalize_card_label(label), 0)

# ========== SESSION STATE ==========
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        "timestamp",
        "winner",      # RED / BLUE / TIE
        "home_card",   # card label for BLUE (home)
        "away_card",   # card label for RED (away)
        "home_value",
        "away_value",
        "home_class",
        "away_class",
        "home_strength",
        "away_strength"
    ])
if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = []

# ========== SIDEBAR: SETTINGS ==========
with st.sidebar:
    st.header("Controles e Configurações")
    if st.button("Resetar histórico"):
        st.session_state.history = pd.DataFrame(columns=[
            "timestamp","winner","home_card","away_card","home_value","away_value",
            "home_class","away_class","home_strength","away_strength"
        ])
        st.session_state.undo_stack = []
    st.write("---")
    csv_data = st.session_state.history.to_csv(index=False)
    st.download_button("Exportar histórico (CSV)", data=csv_data, file_name="history_football_studio.csv")
    st.write("---")
    show_timestamps = st.checkbox("Mostrar timestamps", value=False)
    show_confidence_bar = st.checkbox("Mostrar barra de confiança", value=True)
    analysis_window = st.selectbox("Janela de análise (últimas N jogadas)", options=[3,5,8,10,20,50], index=3)
    break_threshold = st.slider("Limite de break (%) — se >= limite → NÃO APOSTAR", min_value=30, max_value=80, value=DEFAULT_BREAK_THRESHOLD, step=5)
    st.write("---")
    st.caption("Entrada recomendada só quando NÃO houver break (regra OU–OU).")

# ========== INPUT: adicionar rodada com ambas cartas ==========
st.subheader("Registrar rodada — insira as duas cartas (Home = Azul / Away = Vermelho)")

col1, col2, col3 = st.columns([3,3,2])
with col1:
    home_card = st.selectbox("Carta HOME (Azul)", options=CARD_ORDER, index=8, key="home_card_select")
with col2:
    away_card = st.selectbox("Carta AWAY (Vermelho)", options=CARD_ORDER, index=8, key="away_card_select")
with col3:
    if st.button("Adicionar rodada"):
        now = datetime.now()
        hc = normalize_card_label(home_card)
        ac = normalize_card_label(away_card)
        hv = card_value(hc)
        av = card_value(ac)
        hc_class = card_class(hc)
        ac_class = card_class(ac)
        hs = card_strength(hc)
        as_ = card_strength(ac)
        if hv > av:
            winner = "BLUE"
        elif av > hv:
            winner = "RED"
        else:
            winner = "TIE"
        # push undo snapshot
        st.session_state.undo_stack.append(st.session_state.history.copy())
        # append row
        new_row = {
            "timestamp": now,
            "winner": winner,
            "home_card": hc,
            "away_card": ac,
            "home_value": hv,
            "away_value": av,
            "home_class": hc_class,
            "away_class": ac_class,
            "home_strength": hs,
            "away_strength": as_
        }
        st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame([new_row])], ignore_index=True)

# undo
if st.button("Desfazer ultima rodada"):
    if st.session_state.undo_stack:
        st.session_state.history = st.session_state.undo_stack.pop()
    else:
        st.warning("Nada para desfazer.")

st.write("---")

# ========== HISTORY GRID ==========
st.subheader("Histórico (visual)")
history = st.session_state.history.copy()
if history.empty:
    st.info("Sem resultados ainda. Use a entrada acima para registrar rodadas.")
else:
    display = history.tail(MAX_COLS * MAX_LINES).reset_index(drop=True)
    rows = [display.iloc[i:i+MAX_COLS] for i in range(0, len(display), MAX_COLS)]
    for r in rows:
        cols = st.columns(MAX_COLS)
        for idx in range(MAX_COLS):
            with cols[idx]:
                if idx < len(r):
                    row = r.iloc[idx]
                    win = row["winner"]
                    if win == "RED":
                        label = f"🔴 {row['away_card']} ({row['away_class']})"
                    elif win == "BLUE":
                        label = f"🔵 {row['home_card']} ({row['home_class']})"
                    else:
                        label = f"🟡 TIE"
                    if show_timestamps:
                        st.caption(str(row["timestamp"]))
                    st.markdown(f"**{label}**")
                else:
                    st.write("")

st.markdown("---")

# ========== ANALYSIS FUNCTIONS ==========
def detect_patterns(df: pd.DataFrame) -> dict:
    patterns = {"repeticao": False, "alternancia": False, "degrau": False, "quebra_controlada": False, "ciclo": False}
    if df.empty:
        return patterns
    winners = df["winner"].tolist()
    classes = []  # use combined class per winner: winner's card class
    for i,row in df.iterrows():
        if row["winner"] == "BLUE":
            classes.append(row["home_class"])
        elif row["winner"] == "RED":
            classes.append(row["away_class"])
        else:
            classes.append("tie")
    n = len(winners)
    if n >= 3 and winners[-1] == winners[-2] == winners[-3] and winners[-1] != "TIE":
        patterns["repeticao"] = True
    if n >= 4 and winners[-1] == winners[-3] and winners[-2] == winners[-4] and winners[-1] != winners[-2]:
        patterns["alternancia"] = True
    if n >= 6:
        seq = winners[-6:]
        if seq[0] == seq[1] and seq[2] == seq[3] and seq[4] == seq[5] and seq[0] == seq[4]:
            patterns["degrau"] = True
    if n >= 3 and classes[-3] == "baixa" and classes[-2] == "baixa" and classes[-1] == "alta":
        patterns["quebra_controlada"] = True
    if n >= 10:
        last10 = winners[-10:]
        if last10[:5] == last10[5:]:
            patterns["ciclo"] = True
    return patterns

def compute_value_profile(df: pd.DataFrame, window: int = 10) -> dict:
    if df.empty:
        return {"n":0, "count_high":0, "count_med":0, "count_low":0, "avg_value":0.0, "high_ratio":0.0}
    sub = df.tail(window)
    n = len(sub)
    # For profile we use both cards: count high when either winning card is high? We'll count both to profile deck
    # Count highs/meds/lows by winner card (what determined result)
    count_high = 0
    count_med = 0
    count_low = 0
    values = []
    for i,row in sub.iterrows():
        if row["winner"] == "BLUE":
            cls = row["home_class"]
            val = row["home_value"]
        elif row["winner"] == "RED":
            cls = row["away_class"]
            val = row["away_value"]
        else:
            cls = "tie"
            val = max(row["home_value"], row["away_value"])
        values.append(val)
        if cls == "alta":
            count_high += 1
        elif cls == "media":
            count_med += 1
        elif cls == "baixa":
            count_low += 1
    avg_value = float(np.mean(values)) if values else 0.0
    high_ratio = count_high / n if n>0 else 0.0
    return {"n":n, "count_high":count_high, "count_med":count_med, "count_low":count_low, "avg_value":avg_value, "high_ratio":high_ratio}

def detect_break_score(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"break_score":0, "reason":""}
    n = len(df)
    score = 0
    reasons = []
    vp5 = compute_value_profile(df, window=5)
    # many low winning cards in last 5
    if vp5["count_low"] >= 3:
        score += 20
        reasons.append(f"{vp5['count_low']}/5 cartas baixas vencedoras")
    # last winner card baixa
    last = df.iloc[-1]
    last_class = last["home_class"] if last["winner"] == "BLUE" else (last["away_class"] if last["winner"]=="RED" else "tie")
    if last_class == "baixa":
        score += 15
        reasons.append("Última carta vencedora baixa")
    # alternancia acelerada
    recent_winners = df["winner"].tolist()[-6:] if n>=6 else df["winner"].tolist()
    if len(recent_winners) > 1:
        alt = sum(1 for i in range(1,len(recent_winners)) if recent_winners[i] != recent_winners[i-1])
        if (alt / (len(recent_winners)-1)) >= 0.75:
            score += 25
            reasons.append("Alternância acelerada")
    # tie recent
    tie_recent = df["winner"].tolist()[-6:].count("TIE")
    if tie_recent >= 1:
        score += tie_recent * 5
        reasons.append(f"{tie_recent} ties recentes")
    # if many highs recent in last 10 -> reduce break
    vp10 = compute_value_profile(df, window=10)
    if vp10["count_high"] >= 4:
        score -= 10
        reasons.append("Muitas altas recentes (reduz risco)")
    score = int(max(0,min(100,score)))
    return {"break_score":score, "reason":"; ".join(reasons)}

def weighted_probs(df: pd.DataFrame, window: int = 10) -> dict:
    if df.empty:
        return {"red":49.0, "blue":49.0, "tie":2.0, "confidence":0.0}
    sub = df.tail(window).reset_index(drop=True)
    m = len(sub)
    weights = np.linspace(1.0, 0.2, m)
    weights = weights / weights.sum()
    score = {"red":0.0, "blue":0.0, "tie":0.0}
    for i,row in sub.iterrows():
        w = weights[i]
        # determine which card influenced winner for factor
        if row["winner"] == "BLUE":
            factor = card_strength(row["home_card"]) / 5.0
        elif row["winner"] == "RED":
            factor = card_strength(row["away_card"]) / 5.0
        else:
            # tie factor: use both low influence
            factor = 0.6
        if row["winner"] == "RED":
            score["red"] += w * (0.6 + 0.4 * factor)
        elif row["winner"] == "BLUE":
            score["blue"] += w * (0.6 + 0.4 * factor)
        else:
            score["tie"] += w * (0.5 + 0.5 * (1 - factor))
    for k in score:
        score[k] += 1e-9
    total = score["red"] + score["blue"] + score["tie"]
    probs = {k: round((v/total)*100,1) for k,v in score.items()}
    values = np.array(list(score.values()))
    peakness = values.max() / values.sum()
    confidence = float(round(min(0.99, max(0.05, peakness)) * 100, 1))
    probs["confidence"] = confidence
    return probs

def compute_manipulation_level(df: pd.DataFrame) -> int:
    if df.empty:
        return 1
    winners = df["winner"].tolist()
    n = len(winners)
    score = 0.0
    # runs of low winning cards
    vals = []
    for i,row in df.iterrows():
        if row["winner"] == "BLUE":
            vals.append(row["home_class"])
        elif row["winner"] == "RED":
            vals.append(row["away_class"])
        else:
            vals.append("tie")
    low_run = 0
    low_runs_count = 0
    for v in vals:
        if v == "baixa":
            low_run += 1
        else:
            if low_run >= 2:
                low_runs_count += 1
            low_run = 0
    if low_run >= 2:
        low_runs_count += 1
    score += low_runs_count * 1.5
    alternations = sum(1 for i in range(1,n) if winners[i] != winners[i-1])
    score += (alternations / max(1,n-1)) * 3.0
    high_count = sum(1 for v in vals if v == "alta")
    score -= (high_count / n) * 1.5
    tie_count = winners.count("TIE")
    score += (tie_count / n) * 2.0
    lvl = int(min(9, max(1, round(score))))
    return lvl

def make_suggestion(df: pd.DataFrame, break_threshold_percent: int, window: int = 10) -> dict:
    probs = weighted_probs(df, window=window)
    break_info = detect_break_score(df)
    break_score = break_info["break_score"]
    # Rule OU-OU
    if break_score >= break_threshold_percent:
        return {"action":"no_bet", "text":f"NAO APOSTAR - quebra provavel ({break_score}%)", "reason":break_info["reason"], "probs":probs, "break_score":break_score}
    # tie case
    if probs["tie"] >= 12.0:
        return {"action":"bet_tie", "text":"APOSTAR TIE (🟡)", "reason":"Probabilidade de empate elevada", "probs":probs, "break_score":break_score}
    # choose color by prob
    top_color = "RED" if probs["red"] > probs["blue"] else "BLUE"
    top_prob = probs["red"] if top_color=="RED" else probs["blue"]
    confidence = probs["confidence"]
    # adjust thresholds by manipulation level
    manip = compute_manipulation_level(df)
    # If manipulation high, require stronger thresholds
    prob_threshold = 60.0 + (5.0 if manip >= 7 else 0.0)
    conf_threshold = 70.0 + (5.0 if manip >= 7 else 0.0)
    if top_prob >= prob_threshold or confidence >= conf_threshold:
        emoji = "🔴" if top_color=="RED" else "🔵"
        return {"action":"bet_color", "text":f"APOSTAR {top_color} ({emoji}) - prob {top_prob}% / conf {confidence}%", "reason":f"Prob >= {prob_threshold} ou conf >= {conf_threshold}", "probs":probs, "break_score":break_score}
    return {"action":"wait", "text":"AGUARDAR - sem entrada segura", "reason":"Probabilidades insuficientes / manipulação ou break fraco", "probs":probs, "break_score":break_score}

# ========== RUN ANALYSIS ==========
st.subheader("Analise e Previsao")
analysis_df = st.session_state.history.copy()

patterns = detect_patterns(analysis_df)
value_profile = compute_value_profile(analysis_df, window=analysis_window)
break_info = detect_break_score(analysis_df)
probs = weighted_probs(analysis_df, window=analysis_window)
manip_level = compute_manipulation_level(analysis_df)
suggestion = make_suggestion(analysis_df, break_threshold, window=analysis_window)

# ========== DISPLAY ==========
colA, colB = st.columns([2,1])
with colA:
    detected = ", ".join([k for k,v in patterns.items() if v]) or "indefinido"
    st.markdown(f"**Padroes detectados:** {detected}")
    st.markdown(f"**Perfil de valor (ultimas {analysis_window}):** altas {value_profile['count_high']}, medias {value_profile['count_med']}, baixas {value_profile['count_low']}, avg {value_profile['avg_value']:.1f}")
    st.markdown(f"**Nível de manipulacao (1-9):** {manip_level}")
    st.markdown(f"**Break score:** {break_info['break_score']}%")
    if break_info["reason"]:
        st.write(f"Motivos: {break_info['reason']}")
    st.markdown(f"**Sugestao:** {suggestion['text']}")
    if suggestion.get("reason"):
        st.write(f"Observacao: {suggestion.get('reason')}")
with colB:
    st.metric("🔴 RED", f"{probs['red']} %")
    st.metric("🔵 BLUE", f"{probs['blue']} %")
    st.metric("🟡 TIE", f"{probs['tie']} %")
    if show_confidence_bar:
        st.progress(int(min(100, probs["confidence"])))

st.markdown("---")
st.subheader("Resumo das ultimas jogadas (ultimas 30)")
if analysis_df.empty:
    st.info("Nenhum dado para exibir.")
else:
    st.dataframe(analysis_df.tail(30).reset_index(drop=True))

# ========== TOOLS ==========
st.markdown("---")
st.header("Ferramentas")
csv_full = st.session_state.history.to_csv(index=False)
st.download_button("Exportar historico completo (CSV)", data=csv_full, file_name="history_football_studio_full.csv")

if st.button("Gerar relatorio (TXT)"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    detected_list = ", ".join([k for k,v in patterns.items() if v]) or "indefinido"
    txt = f"Football Studio Analyzer - Relatorio Profissional\nGerado em: {now}\n"
    txt += f"Padroes detectados: {detected_list}\n"
    txt += f"Perfil valor (ultimas {analysis_window}): altas {value_profile['count_high']}, medias {value_profile['count_med']}, baixas {value_profile['count_low']}\n"
    txt += f"Break score: {break_info['break_score']}% - {break_info['reason']}\n"
    txt += f"Nivel de manipulacao: {manip_level}\n"
    txt += f"Sugestao: {suggestion['text']}\n"
    txt += f"Probabilidades: RED {probs['red']}%, BLUE {probs['blue']}%, TIE {probs['tie']}%\n"
    txt += f"Confianca: {probs['confidence']}%\n\n"
    txt += "Ultimas 30 jogadas:\n"
    txt += analysis_df.tail(30).to_csv(index=False)
    st.download_button("Baixar relatorio (TXT)", data=txt, file_name="relatorio_football_studio.txt")

st.caption("Analise hibrida: valor das cartas + padrao de cores. Probabilidades sao estimativas; aposte com responsabilidade.")
