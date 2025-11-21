# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ========== CONFIG ==========
st.set_page_config(page_title="Football Studio Analyzer - Profissional", layout="wide")

# Mapeamento e constantes
CARD_MAP = {"A":14, "K":13, "Q":12, "J":11, "10":10, "9":9, "8":8, "7":7, "6":6, "5":5, "4":4, "3":3, "2":2}
HIGH = {"A","K","Q","J"}
MEDIUM = {"10","9","8"}
LOW = {"7","6","5","4","3","2"}
CARD_STRENGTH = {"A":5,"K":5,"Q":5,"J":4,"10":4,"9":3,"8":3,"7":2,"6":1,"5":1,"4":1,"3":1,"2":1}
CARD_ORDER = ["A","K","Q","J","10","9","8","7","6","5","4","3","2"]

MAX_COLS = 9
MAX_LINES = 10

# ========== UTILITARIOS ==========
def card_value(label: str) -> int:
    return CARD_MAP.get(str(label), 0)

def card_group(label: str) -> str:
    if label in HIGH:
        return "alta"
    if label in MEDIUM:
        return "media"
    if label in LOW:
        return "baixa"
    return "tie"

def strength_of(label: str) -> int:
    return CARD_STRENGTH.get(label, 1)

# ========== ESTADO ==========
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["timestamp","winner","card","value","value_class","strength"])

# ========== FUNCOES HISTORICO ==========
def add_result(winner: str, card_label: str):
    now = datetime.now()
    if card_label == "T":
        value = 0
        vclass = "tie"
        strength = 0
    else:
        value = card_value(card_label)
        vclass = card_group(card_label)
        strength = strength_of(card_label)
    new = pd.DataFrame([{"timestamp": now, "winner": winner, "card": card_label, "value": value, "value_class": vclass, "strength": strength}])
    st.session_state.history = pd.concat([st.session_state.history, new], ignore_index=True)

def reset_history():
    st.session_state.history = pd.DataFrame(columns=["timestamp","winner","card","value","value_class","strength"])

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("Controles")
    if st.button("Resetar historico"):
        reset_history()
    st.write("---")
    csv_data = st.session_state.history.to_csv(index=False)
    st.download_button("Exportar historico (CSV)", data=csv_data, file_name="history_football_studio.csv")
    st.write("---")
    show_timestamps = st.checkbox("Mostrar timestamps", value=False)
    show_confidence_bar = st.checkbox("Mostrar barra de confianca", value=True)
    st.markdown("Janela de analise (ultimas N jogadas)")
    analysis_window = st.selectbox("Janela", options=[3,5,8,10,20,50], index=3)

# ========== INSERCAO RAPIDA ==========
st.title("Football Studio Analyzer - Profissional")
st.markdown("Use os botoes abaixo para inserir resultados (1 clique).")

col_red, col_blue, col_tie = st.columns(3)
with col_red:
    st.markdown("<div style='text-align:center; color:#b30000; font-weight:bold;'>RED (VERMELHO)</div>", unsafe_allow_html=True)
    for card in CARD_ORDER:
        if st.button(f"🔴 {card}", key=f"r_{card}"):
            add_result("red", card)

with col_blue:
    st.markdown("<div style='text-align:center; color:#1f4fff; font-weight:bold;'>BLUE (AZUL)</div>", unsafe_allow_html=True)
    for card in CARD_ORDER:
        if st.button(f"🔵 {card}", key=f"b_{card}"):
            add_result("blue", card)

with col_tie:
    st.markdown("<div style='text-align:center; color:#c7a400; font-weight:bold;'>TIE (EMPATE)</div>", unsafe_allow_html=True)
    if st.button("🟡 TIE", key="tie_btn"):
        add_result("tie", "T")

st.write("---")

# ========== HISTORICO VISUAL ==========
st.subheader("Historico (visual)")
history = st.session_state.history.copy()
if len(history) > MAX_COLS * MAX_LINES:
    history = history.tail(MAX_COLS * MAX_LINES).reset_index(drop=True)

if history.empty:
    st.info("Sem resultados ainda. Use os botoes acima para inserir resultados.")
else:
    rows = [history.iloc[i:i+MAX_COLS] for i in range(0, len(history), MAX_COLS)]
    for row_df in rows:
        cols = st.columns(MAX_COLS)
        for idx in range(MAX_COLS):
            with cols[idx]:
                if idx < len(row_df):
                    item = row_df.iloc[idx]
                    if item["winner"] == "red":
                        label = f"🔴 {item['card']} ({item['value_class']})"
                    elif item["winner"] == "blue":
                        label = f"🔵 {item['card']} ({item['value_class']})"
                    else:
                        label = "🟡 TIE"
                    if show_timestamps:
                        st.caption(str(item["timestamp"]))
                    st.markdown(f"**{label}**")
                else:
                    st.write("")

st.markdown("---")

# ========== ANALISE E HEURISTICAS ==========
def detect_patterns(df: pd.DataFrame) -> dict:
    patterns = {"repeticao": False, "alternancia": False, "degrau": False, "quebra_controlada": False, "ciclo": False}
    if df.empty:
        return patterns
    winners = df["winner"].tolist()
    classes = df["value_class"].tolist()
    n = len(df)
    if n >= 3 and winners[-1] == winners[-2] == winners[-3] and winners[-1] != "tie":
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

def compute_manipulation_level(df: pd.DataFrame) -> int:
    if df.empty:
        return 1
    vals = df["value_class"].tolist()
    winners = df["winner"].tolist()
    n = len(df)
    score = 0.0
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
    alternations = sum(1 for i in range(1, n) if winners[i] != winners[i-1])
    score += (alternations / max(1, n-1)) * 3.0
    high_count = sum(1 for v in vals if v == "alta")
    score -= (high_count / n) * 1.5
    tie_count = sum(1 for w in winners if w == "tie")
    score += (tie_count / n) * 2.0
    lvl = int(min(9, max(1, round(score))))
    return lvl

def detect_break_score(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"break_score": 0, "reason": ""}
    classes = df["value_class"].tolist()
    winners = df["winner"].tolist()
    n = len(df)
    score = 0
    reasons = []
    recent = classes[-5:] if n >= 5 else classes
    low_count = sum(1 for x in recent if x == "baixa")
    score += low_count * 15
    if low_count >= 3:
        reasons.append(f"{low_count}/5 baixas recentes")
    if classes[-1] == "baixa":
        score += 15
        reasons.append("Ultima carta baixa")
    recent_winners = winners[-6:] if n >= 6 else winners
    if len(recent_winners) > 1:
        alt = sum(1 for i in range(1, len(recent_winners)) if recent_winners[i] != recent_winners[i-1])
        if (alt / (len(recent_winners)-1)) >= 0.75:
            score += 20
            reasons.append("Alternancia acelerada")
    tie_recent = winners[-5:].count("tie")
    if tie_recent >= 1:
        score += tie_recent * 5
        reasons.append(f"{tie_recent} ties recentes")
    score = min(100, score)
    return {"break_score": score, "reason": "; ".join(reasons)}

def weighted_probs(df: pd.DataFrame, window: int = 10) -> dict:
    if df.empty:
        return {"red":49.0, "blue":49.0, "tie":2.0, "confidence":0.0}
    sub = df.tail(window).reset_index(drop=True)
    m = len(sub)
    weights = np.linspace(1.0, 0.2, m)
    weights = weights / weights.sum()
    score = {"red":0.0, "blue":0.0, "tie":0.0}
    for i, row in sub.iterrows():
        w = weights[i]
        winner = row["winner"]
        if row["card"] == "T":
            factor = 0.6
        else:
            factor = strength_of(row["card"]) / 5.0
        if winner == "red":
            score["red"] += w * (0.6 + 0.4 * factor)
        elif winner == "blue":
            score["blue"] += w * (0.6 + 0.4 * factor)
        else:
            score["tie"] += w * (0.5 + 0.5 * (1 - factor))
    for k in score:
        score[k] += 1e-9
    total = score["red"] + score["blue"] + score["tie"]
    probs = {k: round((v/total)*100,1) for k,v in score.items()}
    values = np.array(list(score.values()))
    peakness = values.max() / values.sum()
    confidence = min(0.99, max(0.05, peakness)) * 100
    return {"red":probs["red"], "blue":probs["blue"], "tie":probs["tie"], "confidence":round(confidence,1)}

def make_suggestion(probs: dict, break_info: dict, manip_level: int) -> dict:
    break_score = break_info.get("break_score", 0)
    reason = break_info.get("reason", "")
    # Regra OU-OU
    if break_score >= 50:
        return {"action":"no_bet", "text":f"NAO APOSTAR - quebra provavel ({break_score}%)", "reason":reason, "confidence":break_score}
    if probs["tie"] >= 12:
        return {"action":"bet_tie", "text":"APOSTAR TIE (🟡)", "reason":reason, "confidence":probs["confidence"]}
    top_color = "red" if probs["red"] > probs["blue"] else "blue"
    if probs[top_color] >= 60 or probs["confidence"] >= 70:
        emoji = "🔴" if top_color=="red" else "🔵"
        return {"action":"bet_color", "text":f"APOSTAR {top_color.upper()} ({emoji})", "reason":reason, "confidence":probs["confidence"]}
    return {"action":"wait", "text":"AGUARDAR - sem entrada segura", "reason":reason, "confidence":probs["confidence"]}

# ========== EXECUCAO ==========
st.subheader("Analise e Previsao")
analysis_df = st.session_state.history.copy()

patterns = detect_patterns(analysis_df)
manip_level = compute_manipulation_level(analysis_df)
break_info = detect_break_score(analysis_df)
probs = weighted_probs(analysis_df, window=analysis_window)
suggestion = make_suggestion(probs, break_info, manip_level)

colA, colB = st.columns([2,1])
with colA:
    detected = ", ".join([k for k,v in patterns.items() if v]) or "indefinido"
    st.markdown(f"**Padroes detectados:** {detected}")
    st.markdown(f"**Nivel de manipulacao (1-9):** {manip_level}")
    # exibicao de sugestao sem ambiguidade
    if suggestion["action"] == "no_bet":
        st.error(suggestion["text"])
        if suggestion["reason"]:
            st.write(f"Motivos: {suggestion['reason']}")
        st.write(f"Confianca (break): {suggestion['confidence']}%")
    elif suggestion["action"] == "bet_tie":
        st.success(suggestion["text"])
        st.write(f"Confianca: {suggestion['confidence']}%")
    elif suggestion["action"] == "bet_color":
        st.success(suggestion["text"])
        st.write(f"Confianca: {suggestion['confidence']}%")
    else:
        st.info(suggestion["text"])
        st.write(f"Confianca: {suggestion['confidence']}%")
    if break_info["break_score"] > 0 and suggestion["action"] != "no_bet":
        st.warning(f"Alerta (break score {break_info['break_score']}%): {break_info['reason']}")
with colB:
    st.metric("RED", f"{probs['red']} %")
    st.metric("BLUE", f"{probs['blue']} %")
    st.metric("TIE", f"{probs['tie']} %")

if show_confidence_bar:
    st.progress(int(min(100, probs["confidence"])))

st.markdown("---")
st.subheader("Resumo das ultimas jogadas (ultimas 30)")
if analysis_df.empty:
    st.info("Nenhum dado para exibir.")
else:
    st.dataframe(analysis_df.tail(30).reset_index(drop=True))

st.markdown("**Interpretacao por valor da carta:**")
st.markdown("- Cartas A,K,Q,J: consideradas ALTAS. Tendem a repetir.")
st.markdown("- Cartas 10,9,8: consideradas MEDIAS. Zona de transicao.")
st.markdown("- Cartas 7-2: consideradas BAIXAS. Maior risco de quebra.")

st.markdown("---")
st.header("Ferramentas")
csv_full = st.session_state.history.to_csv(index=False)
st.download_button("Exportar historico completo (CSV)", data=csv_full, file_name="history_football_studio_full.csv")
if st.button("Gerar relatorio (TXT)"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    detected_list = ", ".join([k for k,v in patterns.items() if v]) or "indefinido"
    txt = f"Football Studio Analyzer - Relatorio Profissional\\nGerado em: {now}\\n"
    txt += f"Padroes detectados: {detected_list}\\n"
    txt += f"Nivel de manipulacao: {manip_level}\\n"
    if suggestion["action"] == "no_bet":
        txt += f"RECOMENDACAO: NAO APOSTAR - Quebra provavel ({break_info['break_score']}%)\\n"
        if break_info["reason"]:
            txt += f"Motivos: {break_info['reason']}\\n"
    else:
        txt += f"RECOMENDACAO: {suggestion['text']}\\n"
    txt += f"Probabilidades: RED {probs['red']}%, BLUE {probs['blue']}%, TIE {probs['tie']}%\\n"
    txt += f"Confianca: {probs['confidence']}%\\n\\n"
    txt += "Ultimas 30 jogadas:\\n"
    txt += analysis_df.tail(30).to_csv(index=False)
    st.download_button("Baixar relatorio (TXT)", data=txt, file_name="relatorio_football_studio.txt")

st.caption("Sistema profissional. Probabilidades sao estimativas; aposte com responsabilidade.")
