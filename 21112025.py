
# football_studio_analyzer_pro.py
# Football Studio Analyzer - Profissional Avançado
# App único (Streamlit) com:
# - Força real das cartas
# - Leitura de padrões combinados (repetição, alternância, degrau, quebra, ciclos)
# - Nível de manipulação (1-9)
# - Detector de quebra (pontuação 0–100)
# - Probabilidades ponderadas RED/BLUE/TIE
# - Sugestão de aposta refinada
# - Inserção rápida com botões coloridos
# - Histórico detalhado e exportação CSV/TXT

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ----------------------------- Configuração -----------------------------
st.set_page_config(page_title="Football Studio Analyzer - Profissional Avançado", layout="wide")
st.title("Football Studio Analyzer — Profissional Avançado")
st.markdown(
    "App profissional para análise de cartas no Football Studio.\n"
    "Use os botões coloridos abaixo para inserir resultados com 1 clique."
)

# ----------------------------- Constantes -----------------------------
CARD_MAP = {
    "A": 14, "K": 13, "Q": 12, "J": 11,
    "10": 10, "9": 9, "8": 8, "7": 7,
    "6": 6, "5": 5, "4": 4, "3": 3, "2": 2
}

HIGH = {"A", "K", "Q", "J"}
MEDIUM = {"10", "9", "8"}
LOW = {"7", "6", "5", "4", "3", "2"}

CARD_STRENGTH = {
    "A": 5, "K": 5, "Q": 5,
    "J": 4, "10": 4,
    "9": 3, "8": 3,
    "7": 2, "6": 1, "5": 1, "4": 1, "3": 1, "2": 1
}

CARD_ORDER = ["A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2"]

MAX_COLS = 9
MAX_LINES = 10

# ----------------------------- Funções utilitárias -----------------------------
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

# ----------------------------- Estado -----------------------------
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        "timestamp", "winner", "card", "value", "value_class"
    ])

# ----------------------------- Histórico -----------------------------
def add_result(winner: str, card_label: str):
    now = datetime.now()
    v = card_value(card_label) if card_label != "T" else 0
    vc = card_group(card_label) if card_label != "T" else "tie"
    new_row = pd.DataFrame([{
        "timestamp": now,
        "winner": winner,
        "card": card_label,
        "value": v,
        "value_class": vc
    }])
    st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)

def reset_history():
    st.session_state.history = pd.DataFrame(columns=[
        "timestamp", "winner", "card", "value", "value_class"
    ])

# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    st.header("Controles")
    if st.button("Resetar Histórico"):
        reset_history()
    st.write("---")
    st.markdown("Exportar / Configurações")
    csv_data = st.session_state.history.to_csv(index=False)
    st.download_button("Exportar histórico (CSV)", data=csv_data, file_name="history_football_studio.csv")
    st.write("---")
    show_timestamps = st.checkbox("Mostrar timestamps", value=False)
    show_confidence_bar = st.checkbox("Mostrar barra de confiança", value=True)
    st.markdown("Janela móvel para análise:")
    analysis_window = st.selectbox("Últimas N jogadas", options=[3, 5, 8, 10, 20, 50], index=3)

# ----------------------------- Inserção rápida -----------------------------
st.subheader("Inserir Resultado — 1 clique")

col_red, col_blue, col_tie = st.columns(3)

with col_red:
    st.markdown("<div style='text-align:center; color:#b30000; font-weight:bold;'>🔴 RED</div>", unsafe_allow_html=True)
    for card in CARD_ORDER:
        if st.button(card, key=f"red_{card}", use_container_width=True):
            add_result("red", card)

with col_blue:
    st.markdown("<div style='text-align:center; color:#1f4fff; font-weight:bold;'>🔵 BLUE</div>", unsafe_allow_html=True)
    for card in CARD_ORDER:
        if st.button(card, key=f"blue_{card}", use_container_width=True):
            add_result("blue", card)

with col_tie:
    st.markdown("<div style='text-align:center; color:#c7a400; font-weight:bold;'>🟡 TIE</div>", unsafe_allow_html=True)
    if st.button("TIE", key="tie_main", use_container_width=True):
        add_result("tie", "T")

st.write("---")

# ----------------------------- Histórico (visualização) -----------------------------
st.subheader("Histórico (últimas inserções)")

history = st.session_state.history.copy()
if len(history) > MAX_COLS * MAX_LINES:
    history = history.tail(MAX_COLS * MAX_LINES).reset_index(drop=True)

if history.empty:
    st.info("Sem resultados ainda. Use os botões acima para inserir resultados.")
else:
    rows = [history.iloc[i:i + MAX_COLS] for i in range(0, len(history), MAX_COLS)]
    for row_df in rows:
        cols = st.columns(MAX_COLS)
        for c_idx in range(MAX_COLS):
            with cols[c_idx]:
                if c_idx < len(row_df):
                    item = row_df.iloc[c_idx]
                    if item["winner"] == "red":
                        label = f"🔴 {item['card']} ({item['value_class']})"
                    elif item["winner"] == "blue":
                        label = f"🔵 {item['card']} ({item['value_class']})"
                    else:
                        label = f"🟡 TIE"
                    if show_timestamps:
                        st.caption(str(item["timestamp"]))
                    st.markdown(f"**{label}**")
                else:
                    st.write("")

# ----------------------------- Padrões e Heurísticas Avançadas -----------------------------
def detect_patterns(df: pd.DataFrame) -> dict:
    """Detecta múltiplos padrões profissionais em paralelo."""
    patterns = {"repeticao": False, "alternancia": False, "degrau": False, "quebra_controlada": False, "ciclo": False}
    if df.empty:
        return patterns

    winners = df["winner"].tolist()
    classes = df["value_class"].tolist()
    n = len(df)

    # Repetição: últimos 3 iguais (exceto tie)
    if n >= 3 and winners[-1] == winners[-2] == winners[-3] and winners[-1] != "tie":
        patterns["repeticao"] = True

    # Alternância: ABAB últimos 4
    if n >= 4 and winners[-1] == winners[-3] and winners[-2] == winners[-4] and winners[-1] != winners[-2]:
        patterns["alternancia"] = True

    # Degrau simples: AABBAA últimos 6
    if n >= 6:
        seq = winners[-6:]
        if seq[0] == seq[1] and seq[2] == seq[3] and seq[4] == seq[5] and seq[0] == seq[4]:
            patterns["degrau"] = True

    # Quebra controlada: baixa, baixa, alta últimas 3 classes
    if n >= 3:
        if classes[-3] == "baixa" and classes[-2] == "baixa" and classes[-1] == "alta":
            patterns["quebra_controlada"] = True

    # Ciclo: repetição de padrão alternância + degrau
    if n >= 10:
        last10 = winners[-10:]
        if last10[:5] == last10[5:]:
            patterns["ciclo"] = True

    return patterns

def compute_manipulation_level(df: pd.DataFrame) -> int:
    """Calcula nível de manipulação 1..9 com histórico ponderado e empates."""
    if df.empty:
        return 1
    vals = df["value_class"].tolist()
    winners = df["winner"].tolist()
    n = len(df)
    score = 0.0

    # Baixas consecutivas
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

    # Alternância
    alternations = sum(1 for i in range(1, n) if winners[i] != winners[i-1])
    score += (alternations / max(1, n-1)) * 3.0

    # Muitas altas reduzem suspeita
    high_count = sum(1 for v in vals if v == "alta")
    score -= (high_count / n) * 1.5

    # Empates aumentam manipulação aparente
    tie_count = sum(1 for w in winners if w == "tie")
    score += (tie_count / n) * 2.0

    lvl = int(min(9, max(1, round(score))))
    return lvl

def detect_break_score(df: pd.DataFrame) -> dict:
    """Pontuação de quebra 0-100 baseado em baixas, alternância e ties."""
    if df.empty:
        return {"break_score": 0, "reason": ""}

    classes = df["value_class"].tolist()
    winners = df["winner"].tolist()
    n = len(df)
    score = 0
    reason = []

    # Últimas 5 cartas
    recent = classes[-5:]
    low_count = sum(1 for x in recent if x == "baixa")
    score += low_count * 15
    if low_count >= 3:
        reason.append(f"{low_count}/5 baixas recentes")

    # Última carta baixa
    if classes[-1] == "baixa":
        score += 15
        reason.append("Última carta baixa")

    # Alternância rápida últimos 6
    recent_winners = winners[-6:] if n >= 6 else winners
    alt = sum(1 for i in range(1, len(recent_winners)) if recent_winners[i] != recent_winners[i-1])
    if len(recent_winners) > 1 and (alt / (len(recent_winners)-1)) >= 0.75:
        score += 20
        reason.append("Alternância acelerada")

    # Normalizar 0-100
    score = min(100, score)
    return {"break_score": score, "reason": "; ".join(reason)}

def weighted_probs(df: pd.DataFrame, window: int = 10) -> dict:
    """Calcula probabilidades RED/BLUE/TIE ponderadas por força e padrão."""
    if df.empty:
        return {"red": 49.0, "blue": 49.0, "tie": 2.0, "confidence": 0.0}

    sub = df.tail(window).reset_index(drop=True)
    m = len(sub)
    weights = np.linspace(1, 0.2, m)
    weights = weights / weights.sum()
    score = {"red":0.0, "blue":0.0, "tie":0.0}

    for i, row in sub.iterrows():
        w = weights[i]
        winner = row["winner"]
        factor = strength_of(row["card"]) / 5.0 if row["card"] != "T" else 0.6
        if winner == "red":
            score["red"] += w * (0.6 + 0.4 * factor)
        elif winner == "blue":
            score["blue"] += w * (0.6 + 0.4 * factor)
        else:
            score["tie"] += w * (0.5 + 0.5 * (1 - factor))

    total = sum(score.values())
    probs = {k: round((v/total)*100,1) for k,v in score.items()}

    # Confiança baseada em pico e consistência
    values = np.array(list(score.values()))
    peakness = values.max()/values.sum()
    confidence = min(0.99, max(0.05, peakness)) * 100
    return {"red": probs["red"], "blue": probs["blue"], "tie": probs["tie"], "confidence": round(confidence,1)}

def make_suggestion(probs: dict, break_info: dict, manip_level: int) -> str:
    """Sugestão profissional de aposta considerando probabilidades, break e manipulação."""
    # Break forte
    if break_info.get("break_score",0) >= 50:
        if probs["tie"] >= 12:
            return "apostar TIE (🟡)"
        if probs["red"] > probs["blue"]:
            return "apostar BLUE (🔵) — quebra provável"
        else:
            return "apostar RED (🔴) — quebra provável"

    # Probabilidade segura
    top = max(("red", probs["red"]), ("blue", probs["blue"]), key=lambda x: x[1])
    if probs["tie"] >= 12:
        return "apostar TIE (🟡)"
    if top[1] >= 60 or probs["confidence"] >= 70:
        return f"apostar {top[0].upper()} ({'🔴' if top[0]=='red' else '🔵'})"
    return "aguardar (sem entrada segura)"

# ----------------------------- Execução da análise -----------------------------
st.subheader("Análise e Previsão")

analysis_df = st.session_state.history.copy()
patterns = detect_patterns(analysis_df)
manip_level = compute_manipulation_level(analysis_df)
break_info = detect_break_score(analysis_df)
probs = weighted_probs(analysis_df, window=analysis_window)
suggestion = make_suggestion(probs, break_info, manip_level)

colA, colB = st.columns([2,1])
with colA:
    st.markdown(f"**Padrões detectados:** {', '.join([k for k,v in patterns.items() if v]) or 'indefinido'}")
    st.markdown(f"**Nível de manipulação (1–9):** {manip_level}")
    st.markdown(f"**Sugestão:** {suggestion}")
    st.markdown(f"**Confiança:** {probs['confidence']} %")
    if break_info["break_score"] >= 50:
        st.warning(f"QUEBRA DETECTADA ({break_info['break_score']}%): {break_info['reason']}")

with colB:
    st.metric("🔴 RED", f"{probs['red']} %")
    st.metric("🔵 BLUE", f"{probs['blue']} %")
    st.metric("🟡 TIE", f"{probs['tie']} %")

if show_confidence_bar:
    st.progress(int(min(100, probs['confidence'])))

# ----------------------------- Últimas jogadas -----------------------------
st.subheader("Resumo últimas 10 jogadas")
st.dataframe(analysis_df.tail(10).reset_index(drop=True))

st.markdown("**Interpretação por valor da carta:**")
st.markdown("""
- **A,K,Q,J** → ALTAS: tendem a repetir.  
- **10,9,8** → MÉDIAS: observar padrão.  
- **7–2** → BAIXAS: alto risco de quebra, evite cor atual.  
""")
st.markdown("**Estratégia:** siga padrão, janela de análise, confiança >=70%, evite apostas em break forte.")

# ----------------------------- Exportação avançada -----------------------------
st.markdown("---")
st.header("Ferramentas")

if st.button("Gerar relatório (TXT)"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    txt = f"Football Studio Analyzer - Relatório Profissional\nGerado em: {now}\n"
    txt += f"Padrões detectados: {', '.join([k for k,v in patterns.items() if v]) or 'indefinido'}\n"
    txt += f"Nível de manipulação: {manip_level}\n"
    txt += f"Sugestão: {suggestion}\n"
    txt += f"Probabilidades: RED {probs['red']}%, BLUE {probs['blue']}%, TIE {probs['tie']}%\n"
    txt += f"Confiança: {probs['confidence']}%\n"
    if break_info["break_score"] >= 50:
        txt += f"QUEBRA: {break_info['break_score']}% — {break_info['reason']}\n"
    txt += "\nÚltimas 30 jogadas:\n"
    txt += analysis_df.tail(30).to_csv(index=False)
    st.download_button("Baixar relatório (TXT)", data=txt, file_name="relatorio_football_studio.txt")

st.markdown("---")
st.caption("Sistema profissional baseado em valor das cartas, padrões e manipulação. Probabilidades são estimativas; aposte com responsabilidade.")
