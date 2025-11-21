import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ========== Config ==========
st.set_page_config(page_title="Football Studio Pro - Completo (Opção A)", layout="wide")
st.title("Football Studio Pro — Valor + Padrão (Opção A: Casa x Visitante)")

# ========== Constantes ==========
CARD_ORDER = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
CARD_MAP = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"10":10,"J":11,"Q":12,"K":13,"A":14}
HIGH = {"A","K","Q","J"}
MEDIUM = {"10","9","8"}
LOW = {"7","6","5","4","3","2"}
CARD_STRENGTH = {"A":5,"K":5,"Q":5,"J":4,"10":4,"9":3,"8":3,"7":2,"6":1,"5":1,"4":1,"3":1,"2":1}

MAX_DISPLAY = 90

# ========== Estado ==========
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        "timestamp","winner","home_card","away_card",
        "home_value","away_value","home_class","away_class",
        "home_strength","away_strength"
    ])
if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = []
# selections for quick horizontal input (keeps currently selected card for each side)
if "sel_home" not in st.session_state:
    st.session_state.sel_home = None
if "sel_away" not in st.session_state:
    st.session_state.sel_away = None

# ========== Sidebar ==========
with st.sidebar:
    st.header("Controles e Configurações")
    if st.button("Resetar histórico"):
        st.session_state.undo_stack.append(st.session_state.history.copy())
        st.session_state.history = st.session_state.history.iloc[0:0]
        st.session_state.sel_home = None
        st.session_state.sel_away = None
        st.success("Histórico resetado.")
    st.write("---")
    csv_data = st.session_state.history.to_csv(index=False)
    st.download_button("Exportar histórico (CSV)", data=csv_data, file_name="history_football_studio.csv")
    st.write("---")
    show_timestamps = st.checkbox("Mostrar timestamps", value=False)
    show_confidence_bar = st.checkbox("Mostrar barra de confiança", value=True)
    analysis_window = st.selectbox("Janela de análise (últimas N jogadas)", options=[3,5,8,10,20,50], index=3)
    break_threshold = st.slider("Limite de break (%) para alerta forte", min_value=30, max_value=80, value=50, step=5)
    st.write("---")
    st.caption("Home = VERMELHO (RED). Visitante = AZUL (BLUE). Opção A: registra as duas cartas por rodada.")

# ========== Helpers ==========
def normalize(card):
    return str(card).strip().upper()

def card_value(card):
    return CARD_MAP.get(normalize(card), 0)

def card_class(card):
    c = normalize(card)
    if c in HIGH:
        return "alta"
    if c in MEDIUM:
        return "media"
    if c in LOW:
        return "baixa"
    return "tie"

def card_strength(card):
    return CARD_STRENGTH.get(normalize(card), 0)

def push_undo():
    st.session_state.undo_stack.append(st.session_state.history.copy())

def append_round(home_card, away_card):
    now = datetime.now()
    hc = normalize(home_card)
    ac = normalize(away_card)
    hv = card_value(hc)
    av = card_value(ac)
    hc_class = card_class(hc)
    ac_class = card_class(ac)
    hs = card_strength(hc)
    as_ = card_strength(ac)
    if hv > av:
        winner = "RED"  # CASA = VERMELHO
    elif av > hv:
        winner = "BLUE"
    else:
        winner = "TIE"
    row = {
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
    push_undo()
    st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame([row])], ignore_index=True)
    # reset quick selections
    st.session_state.sel_home = None
    st.session_state.sel_away = None

# ========== Input panel (horizontal compact) ==========
st.subheader("Inserção rápida — selecione CASA (vermelho) e VISITANTE (azul). Ao ter ambos, a rodada é registrada automaticamente.")

# Home (Casa) horizontal buttons
st.markdown("**🔴 CASA (VERMELHO)**")
cols_home = st.columns(len(CARD_ORDER))
for i, val in enumerate(CARD_ORDER):
    with cols_home[i]:
        if st.button(val, key=f"home_btn_{val}"):
            st.session_state.sel_home = val
            st.success(f"Selecionado CASA {val}")
            # if away already selected, append immediately
            if st.session_state.sel_away:
                append_round(st.session_state.sel_home, st.session_state.sel_away)

# Away (Visitante) horizontal buttons
st.markdown("**🔵 VISITANTE (AZUL)**")
cols_away = st.columns(len(CARD_ORDER))
for i, val in enumerate(CARD_ORDER):
    with cols_away[i]:
        if st.button(val, key=f"away_btn_{val}"):
            st.session_state.sel_away = val
            st.success(f"Selecionado VISITANTE {val}")
            # if home already selected, append immediately
            if st.session_state.sel_home:
                append_round(st.session_state.sel_home, st.session_state.sel_away)

# Visual of current quick selection
sel_home = st.session_state.sel_home or "-"
sel_away = st.session_state.sel_away or "-"
st.info(f"Selecionado agora: CASA {sel_home}  —  VISITANTE {sel_away}")

# Quick 1-clique (dropdown) — alternativa
st.markdown("---")
st.subheader("Adicionar rodada em 1 clique (opcional)")
c1, c2, c3 = st.columns([3,3,2])
with c1:
    quick_home = st.selectbox("Casa (VERMELHO)", options=CARD_ORDER, index=0, key="quick_home")
with c2:
    quick_away = st.selectbox("Visitante (AZUL)", options=CARD_ORDER, index=0, key="quick_away")
with c3:
    if st.button("Adicionar rodada (1 clique)"):
        append_round(quick_home, quick_away)
        st.success(f"Rodada adicionada: CASA {quick_home} vs VISITANTE {quick_away}")

# undo / clear controls
st.markdown("---")
cundo, cclear = st.columns([1,1])
with cundo:
    if st.button("Desfazer ultima"):
        if st.session_state.undo_stack:
            st.session_state.history = st.session_state.undo_stack.pop()
            st.success("Última ação desfeita.")
        else:
            st.warning("Nada para desfazer.")
with cclear:
    if st.button("Limpar tudo"):
        st.session_state.undo_stack.append(st.session_state.history.copy())
        st.session_state.history = st.session_state.history.iloc[0:0]
        st.session_state.sel_home = None
        st.session_state.sel_away = None
        st.success("Limpo.")

st.markdown("---")

# ========== Display history grid ==========
st.subheader("Histórico (visual) — últimas entradas")
history = st.session_state.history.copy()
if history.empty:
    st.info("Sem entradas ainda.")
else:
    display = history.tail(MAX_DISPLAY).reset_index(drop=True)
    rows = [display.iloc[i:i+9] for i in range(0, len(display), 9)]
    for row_df in rows:
        cols = st.columns(9)
        for c_idx in range(9):
            with cols[c_idx]:
                if c_idx < len(row_df):
                    r = row_df.iloc[c_idx]
                    if r["winner"] == "RED":
                        label = f"🔴 {r['home_card']} vs {r['away_card']} ({r['home_class']})"
                    elif r["winner"] == "BLUE":
                        label = f"🔵 {r['home_card']} vs {r['away_card']} ({r['away_class']})"
                    else:
                        label = f"🟡 {r['home_card']} vs {r['away_card']} (TIE)"
                    if show_timestamps:
                        st.caption(str(r["timestamp"]))
                    st.markdown(f"**{label}**")
                else:
                    st.write("")

st.markdown("---")

# ========== Analysis functions ==========
def detect_patterns(df):
    patterns = {"repeticao": False, "alternancia": False, "degrau": False, "quebra_controlada": False, "ciclo": False}
    if df.empty:
        return patterns
    winners = df["winner"].tolist()
    classes = []
    for i,row in df.iterrows():
        if row["winner"] == "RED":
            classes.append(row["home_class"])
        elif row["winner"] == "BLUE":
            classes.append(row["away_class"])
        else:
            classes.append("tie")
    n = len(winners)
    if n >= 3 and winners[-1] == winners[-2] == winners[-3] and winners[-1] != "TIE" and winners[-1] is not None:
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

def compute_value_profile(df, window=10):
    if df.empty:
        return {"n":0,"count_high":0,"count_med":0,"count_low":0,"avg_value":0.0,"high_ratio":0.0}
    sub = df.tail(window)
    n = len(sub)
    count_high = 0; count_med = 0; count_low = 0
    values = []
    for i,row in sub.iterrows():
        if row["winner"] == "RED":
            cls = row["home_class"]; val = row["home_value"]
        elif row["winner"] == "BLUE":
            cls = row["away_class"]; val = row["away_value"]
        else:
            cls = "tie"; val = max(row["home_value"] if not pd.isna(row["home_value"]) else 0, row["away_value"] if not pd.isna(row["away_value"]) else 0)
        values.append(val)
        if cls == "alta": count_high += 1
        elif cls == "media": count_med += 1
        elif cls == "baixa": count_low += 1
    avg_value = float(np.mean(values)) if values else 0.0
    high_ratio = count_high / n if n>0 else 0.0
    return {"n":n,"count_high":count_high,"count_med":count_med,"count_low":count_low,"avg_value":avg_value,"high_ratio":high_ratio}

def detect_break_score(df):
    if df.empty:
        return {"break_score":0,"reason":""}
    n = len(df)
    score = 0
    reasons = []
    vp5 = compute_value_profile(df, window=5)
    if vp5["count_low"] >= 3:
        score += 20; reasons.append(f"{vp5['count_low']}/5 cartas baixas vencedoras")
    last = df.iloc[-1]
    last_class = None
    if last["winner"] == "RED":
        last_class = last["home_class"]
    elif last["winner"] == "BLUE":
        last_class = last["away_class"]
    else:
        last_class = "tie"
    if last_class == "baixa":
        score += 15; reasons.append("Ultima carta vencedora baixa")
    recent = df["winner"].tolist()[-6:] if n>=6 else df["winner"].tolist()
    if len(recent) > 1:
        alt = sum(1 for i in range(1,len(recent)) if recent[i] != recent[i-1])
        if (alt / (len(recent)-1)) >= 0.75:
            score += 25; reasons.append("Alternancia acelerada")
    tie_recent = df["winner"].tolist()[-6:].count("TIE")
    if tie_recent >= 1:
        score += tie_recent * 5; reasons.append(f"{tie_recent} ties recentes")
    vp10 = compute_value_profile(df, window=10)
    if vp10["count_high"] >= 4:
        score -= 10; reasons.append("Muitas altas recentes (reduz risco)")
    score = int(max(0,min(100,score)))
    return {"break_score":score,"reason":"; ".join(reasons)}

def weighted_probs(df, window=10):
    if df.empty:
        return {"red":49.0,"blue":49.0,"tie":2.0,"confidence":0.0}
    sub = df.tail(window).reset_index(drop=True)
    m = len(sub)
    weights = np.linspace(1.0,0.2,m)
    weights = weights / weights.sum()
    scr = {"red":0.0,"blue":0.0,"tie":0.0}
    for i,row in sub.iterrows():
        w = weights[i]
        if row["winner"] == "RED":
            factor = CARD_STRENGTH.get(row["home_card"],1)/5.0 if row["home_card"] else 0.6
            scr["red"] += w * (0.6 + 0.4 * factor)
        elif row["winner"] == "BLUE":
            factor = CARD_STRENGTH.get(row["away_card"],1)/5.0 if row["away_card"] else 0.6
            scr["blue"] += w * (0.6 + 0.4 * factor)
        else:
            factor = 0.6
            scr["tie"] += w * (0.5 + 0.5 * (1 - factor))
    for k in scr: scr[k] += 1e-9
    total = scr["red"] + scr["blue"] + scr["tie"]
    probs = {k: round((v/total)*100,1) for k,v in scr.items()}
    values = np.array(list(scr.values()))
    peakness = values.max() / values.sum()
    confidence = float(round(min(0.99, max(0.05, peakness)) * 100, 1))
    probs["confidence"] = confidence
    return probs

def compute_manipulation_level(df):
    if df.empty:
        return 1
    winners = df["winner"].tolist()
    n = len(winners)
    vals = []
    for i,row in df.iterrows():
        if row["winner"] == "RED":
            vals.append(row["home_class"])
        elif row["winner"] == "BLUE":
            vals.append(row["away_class"])
        else:
            vals.append("tie")
    score = 0.0
    low_run = 0; low_runs_count = 0
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

def make_suggestion(df, window=10):
    if df.empty:
        return {"action":"wait","text":"AGUARDAR - sem dados","probs":{"red":49.0,"blue":49.0,"tie":2.0,"confidence":0.0},"break_score":0}
    probs = weighted_probs(df, window=window)
    break_info = detect_break_score(df)
    break_score = break_info["break_score"]
    patterns = detect_patterns(df)
    manip = compute_manipulation_level(df)
    any_pattern = any(patterns.values())
    top_color = "RED" if probs["red"] > probs["blue"] else "BLUE"
    top_prob = probs["red"] if top_color=="RED" else probs["blue"]
    conf = probs["confidence"]
    if probs["tie"] >= 12.0:
        return {"action":"bet_tie","text":f"APOSTAR TIE (🟡) - prob {probs['tie']}%","probs":probs,"break_score":break_score}
    if any_pattern or top_prob >= 55.0 or conf >= 50.0:
        emoji = "🔴" if top_color=="RED" else "🔵"
        text = f"APOSTAR {top_color} ({emoji}) - prob {top_prob}% / conf {conf}%"
        if break_score >= break_threshold:
            text += f"  ⚠ BREAK {break_score}%"
        return {"action":"bet_color","text":text,"probs":probs,"break_score":break_score}
    return {"action":"wait","text":"AGUARDAR - sem entrada segura","probs":probs,"break_score":break_score}

# ========== Run analysis & display ==========
st.subheader("Analise e Previsao (Modo Agressivo)")

analysis_df = st.session_state.history.copy()
patterns = detect_patterns(analysis_df)
value_profile = compute_value_profile(analysis_df, window=analysis_window)
break_info = detect_break_score(analysis_df)
probs = weighted_probs(analysis_df, window=analysis_window)
manip_level = compute_manipulation_level(analysis_df)
suggestion = make_suggestion(analysis_df, window=analysis_window)

colA, colB = st.columns([2,1])
with colA:
    detected = ", ".join([k for k,v in patterns.items() if v]) or "indefinido"
    st.markdown(f"**Padroes detectados:** {detected}")
    st.markdown(f"**Perfil de valor (ultimas {analysis_window}):** altas {value_profile['count_high']}, medias {value_profile['count_med']}, baixas {value_profile['count_low']}, avg {value_profile['avg_value']:.1f}")
    st.markdown(f"**Nivel de manipulacao (1-9):** {manip_level}")
    st.markdown(f"**Break score:** {break_info['break_score']}%")
    if break_info["reason"]:
        st.write(f"Motivos: {break_info['reason']}")
    st.markdown(f"**Sugestao:** {suggestion['text']}")
    if suggestion.get("probs"):
        st.write(f"Observacao: {suggestion.get('probs')}")
with colB:
    st.metric("🔴 RED (CASA)", f"{probs['red']} %")
    st.metric("🔵 BLUE (VISITANTE)", f"{probs['blue']} %")
    st.metric("🟡 TIE", f"{probs['tie']} %")
    if show_confidence_bar:
        st.progress(int(min(100, probs["confidence"])))

st.markdown("---")
st.subheader("Resumo das ultimas jogadas (ultimas 30)")
if analysis_df.empty:
    st.info("Nenhum dado para exibir.")
else:
    st.dataframe(analysis_df.tail(30).reset_index(drop=True))

# ========== Tools ==========
st.markdown("---")
st.header("Ferramentas")
csv_full = st.session_state.history.to_csv(index=False)
st.download_button("Exportar historico completo (CSV)", data=csv_full, file_name="history_full.csv")

if st.button("Gerar relatorio (TXT)"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    detected_list = ", ".join([k for k,v in patterns.items() if v]) or "indefinido"
    txt = f"Football Studio Pro - Relatorio\nGerado em: {now}\n"
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

st.caption("Analise hibrida: valor das cartas + padrao de cores. Modo agressivo. Probabilidades sao estimativas; aposte com responsabilidade.")
