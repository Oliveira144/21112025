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
def card_value(label: str) -> int:
    return CARD_MAP.get(str(label), 0)

def card_class(label: str) -> str:
    if label in HIGH:
        return "alta"
    if label in MEDIUM:
        return "media"
    if label in LOW:
        return "baixa"
    return "tie"

def card_strength(label: str) -> int:
    return CARD_STRENGTH.get(label, 0)

# ========== SESSION STATE ==========
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["timestamp","winner","card","value","value_class","strength"])
if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = []

# ========== SIDEBAR: SETTINGS ==========
with st.sidebar:
    st.header("Controles e Configurações")
    if st.button("Resetar histórico"):
        st.session_state.history = pd.DataFrame(columns=["timestamp","winner","card","value","value_class","strength"])
        st.session_state.undo_stack = []
    st.write("---")
    st.markdown("Exportar / Visual")
    csv_data = st.session_state.history.to_csv(index=False)
    st.download_button("Exportar histórico (CSV)", data=csv_data, file_name="history_football_studio.csv")
    st.write("---")
    show_timestamps = st.checkbox("Mostrar timestamps", value=False)
    show_confidence_bar = st.checkbox("Mostrar barra de confiança", value=True)
    analysis_window = st.selectbox("Janela de análise (últimas N jogadas)", options=[3,5,8,10,20,50], index=3)
    break_threshold = st.slider("Limite de break (percent) - regra NAO APOSTAR", min_value=30, max_value=80, value=DEFAULT_BREAK_THRESHOLD, step=5)
    st.write("---")
    st.caption("Regra OU-OU: se break_score >= limite -> NAO APOSTAR.")

# ========== INPUT AREA ==========
st.subheader("Inserir resultado (1 clique) — Escolha carta e cor")
cols = st.columns(3)
with cols[0]:
    st.markdown("**🔴 RED (Vermelho)**")
    for c in CARD_ORDER:
        if st.button(f"🔴 {c}", key=f"red_{c}"):
            # add red result
            now = datetime.now()
            row = {"timestamp": now, "winner": "RED", "card": c, "value": card_value(c), "value_class": card_class(c), "strength": card_strength(c)}
            st.session_state.undo_stack.append(st.session_state.history.copy())
            st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame([row])], ignore_index=True)

with cols[1]:
    st.markdown("**🔵 BLUE (Azul)**")
    for c in CARD_ORDER:
        if st.button(f"🔵 {c}", key=f"blue_{c}"):
            now = datetime.now()
            row = {"timestamp": now, "winner": "BLUE", "card": c, "value": card_value(c), "value_class": card_class(c), "strength": card_strength(c)}
            st.session_state.undo_stack.append(st.session_state.history.copy())
            st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame([row])], ignore_index=True)

with cols[2]:
    st.markdown("**🟡 TIE (Empate)**")
    if st.button("🟡 TIE", key="tie_btn"):
        now = datetime.now()
        row = {"timestamp": now, "winner": "TIE", "card": "T", "value": 0, "value_class": "tie", "strength": 0}
        st.session_state.undo_stack.append(st.session_state.history.copy())
        st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame([row])], ignore_index=True)

# undo last
if st.button("Desfazer ultima entrada"):
    if st.session_state.undo_stack:
        st.session_state.history = st.session_state.undo_stack.pop()
    else:
        st.warning("Nada para desfazer.")

st.write("---")

# ========== DISPLAY HISTORY (GRID) ==========
st.subheader("Historico (visual)")
history = st.session_state.history.copy()
if history.empty:
    st.info("Sem resultados. Insira usando os botoes acima.")
else:
    # limit display
    display = history.tail(MAX_COLS * MAX_LINES).reset_index(drop=True)
    rows = [display.iloc[i:i+MAX_COLS] for i in range(0, len(display), MAX_COLS)]
    for row_df in rows:
        cols = st.columns(MAX_COLS)
        for i in range(MAX_COLS):
            with cols[i]:
                if i < len(row_df):
                    item = row_df.iloc[i]
                    if item["winner"] == "RED":
                        label = f"🔴 {item['card']} ({item['value_class']})"
                    elif item["winner"] == "BLUE":
                        label = f"🔵 {item['card']} ({item['value_class']})"
                    else:
                        label = "🟡 TIE"
                    if show_timestamps:
                        st.caption(str(item["timestamp"]))
                    st.markdown(f"**{label}**")
                else:
                    st.write("")

st.markdown("---")

# ========== ANALYSIS MODULES ==========
def detect_patterns(df: pd.DataFrame) -> dict:
    patterns = {"repeticao": False, "alternancia": False, "degrau": False, "quebra_controlada": False, "ciclo": False}
    if df.empty:
        return patterns
    winners = df["winner"].tolist()
    classes = df["value_class"].tolist()
    n = len(df)
    # repeticao: ultimos 3 iguais (exceto tie)
    if n >= 3 and winners[-1] == winners[-2] == winners[-3] and winners[-1] != "TIE":
        patterns["repeticao"] = True
    # alternancia: ABAB nos ultimos 4
    if n >= 4 and winners[-1] == winners[-3] and winners[-2] == winners[-4] and winners[-1] != winners[-2]:
        patterns["alternancia"] = True
    # degrau: A A B B A A
    if n >= 6:
        seq = winners[-6:]
        if seq[0] == seq[1] and seq[2] == seq[3] and seq[4] == seq[5] and seq[0] == seq[4]:
            patterns["degrau"] = True
    # quebra controlada: baixa, baixa, alta (ultimas 3 classes)
    if n >= 3 and classes[-3] == "baixa" and classes[-2] == "baixa" and classes[-1] == "alta":
        patterns["quebra_controlada"] = True
    # ciclo simples
    if n >= 10:
        last10 = winners[-10:]
        if last10[:5] == last10[5:]:
            patterns["ciclo"] = True
    return patterns

def compute_value_profile(df: pd.DataFrame, window: int = 10) -> dict:
    """
    Analisar valores das cartas na janela: conta altas, medias, baixas, media de valor,
    e um indicador de 'baralho drenado' (muitos altos ja sairam -> maior chance de quebra).
    """
    if df.empty:
        return {"n":0, "count_high":0, "count_med":0, "count_low":0, "avg_value":0.0, "high_ratio":0.0}
    sub = df.tail(window)
    n = len(sub)
    count_high = sum(1 for v in sub["value_class"] if v == "alta")
    count_med = sum(1 for v in sub["value_class"] if v == "media")
    count_low = sum(1 for v in sub["value_class"] if v == "baixa")
    avg_value = sub["value"].mean() if n>0 else 0.0
    high_ratio = count_high / n if n>0 else 0.0
    return {"n":n, "count_high":count_high, "count_med":count_med, "count_low":count_low, "avg_value":avg_value, "high_ratio":high_ratio}

def detect_break_score(df: pd.DataFrame) -> dict:
    """
    Combina sinais de valor + padrao para gerar break score (0..100).
    Ex.: muitas cartas baixas recentes + alternancia acelerada + pocas cartas altas -> aumenta break.
    """
    if df.empty:
        return {"break_score":0, "reason":""}
    n = len(df)
    # pattern signals
    patterns = detect_patterns(df)
    score = 0
    reasons = []
    # recent value profile
    vp = compute_value_profile(df, window=5)
    # many low cards in last 5 -> add risk
    if vp["count_low"] >= 3:
        score += 20
        reasons.append(f"{vp['count_low']}/5 cartas baixas")
    # last card baixa -> add risk
    if df.iloc[-1]["value_class"] == "baixa":
        score += 15
        reasons.append("Ultima carta baixa")
    # alternancia acelerada
    recent_winners = df["winner"].tolist()[-6:] if n>=6 else df["winner"].tolist()
    if len(recent_winners) > 1:
        alt = sum(1 for i in range(1, len(recent_winners)) if recent_winners[i] != recent_winners[i-1])
        if (alt / (len(recent_winners)-1)) >= 0.75:
            score += 25
            reasons.append("Alternancia acelerada")
    # many ties recently
    tie_recent = df["winner"].tolist()[-6:].count("TIE")
    if tie_recent >= 1:
        score += tie_recent * 5
        reasons.append(f"{tie_recent} ties recentes")
    # if many highs already in window -> reduce break (deck has fortes)
    vp10 = compute_value_profile(df, window=10)
    if vp10["count_high"] >= 4:
        score -= 10
        reasons.append("Muitas altas recentes (reduz risco)")
    # clamp
    score = int(max(0, min(100, score)))
    return {"break_score": score, "reason": "; ".join(reasons)}

def weighted_probs(df: pd.DataFrame, window: int = 10) -> dict:
    """
    Probabilidades ponderadas por recencia e por força da carta.
    Nota: sao estimativas, usaremos para decidir somente se break_score < threshold.
    """
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
        factor = 0.6 if row["card"] == "T" else (card_strength(row["card"]) / 5.0)
        if winner == "RED":
            score["red"] += w * (0.6 + 0.4 * factor)
        elif winner == "BLUE":
            score["blue"] += w * (0.6 + 0.4 * factor)
        else:
            score["tie"] += w * (0.5 + 0.5 * (1 - factor))
    # normalize
    for k in score:
        score[k] += 1e-9
    total = score["red"] + score["blue"] + score["tie"]
    probs = {k: round((v/total)*100,1) for k,v in score.items()}
    values = np.array(list(score.values()))
    peakness = values.max() / values.sum()
    confidence = float(round(min(0.99, max(0.05, peakness)) * 100, 1))
    probs["confidence"] = confidence
    return probs

def make_suggestion(df: pd.DataFrame, break_threshold_percent: int, window: int = 10) -> dict:
    """
    Combina tudo e retorna sugestao clara:
    - action: "no_bet" / "bet_color" / "bet_tie" / "wait"
    - text: texto de exibicao
    - reason: motivos
    - probs: probabilidades calculadas
    - break_score: int
    """
    analysis = {}
    probs = weighted_probs(df, window=window)
    break_info = detect_break_score(df)
    break_score = break_info["break_score"]
    analysis["break_score"] = break_score
    analysis["break_reason"] = break_info["reason"]
    analysis["probs"] = probs

    # OU-OU rule: if break >= threshold -> no bet
    if break_score >= break_threshold_percent:
        return {"action":"no_bet", "text":f"NAO APOSTAR - quebra provavel ({break_score}%)", "reason": break_info["reason"], "probs":probs, "break_score":break_score}

    # If tie probability high -> bet tie
    if probs["tie"] >= 12.0:
        return {"action":"bet_tie", "text":"APOSTAR TIE (🟡)", "reason":"Probabilidade de empate elevada", "probs":probs, "break_score":break_score}

    # choose color by weighted prob
    top_color = "RED" if probs["red"] > probs["blue"] else "BLUE"
    top_prob = probs["red"] if top_color == "RED" else probs["blue"]
    confidence = probs["confidence"]

    # thresholds to accept entry
    if top_prob >= 60.0 or confidence >= 70.0:
        emoji = "🔴" if top_color == "RED" else "🔵"
        return {"action":"bet_color", "text":f"APOSTAR {top_color} ({emoji}) - prob {top_prob}% / conf {confidence}%", "reason":"Probabilidade e confianca elevadas", "probs":probs, "break_score":break_score}

    # otherwise wait
    return {"action":"wait", "text":"AGUARDAR - sem entrada segura", "reason":"Probabilidades insuficientes", "probs":probs, "break_score":break_score}

# ========== RUN ANALYSIS ==========
st.subheader("Analise e Previsao")
analysis_df = st.session_state.history.copy()

patterns = detect_patterns(analysis_df)
value_profile = compute_value_profile(analysis_df, window=analysis_window)
break_info = detect_break_score(analysis_df)
probs = weighted_probs(analysis_df, window=analysis_window)
suggestion = make_suggestion(analysis_df, break_threshold, window=analysis_window)

# ========== DISPLAY RESULTS ==========
colA, colB = st.columns([2,1])
with colA:
    detected = ", ".join([k for k,v in patterns.items() if v]) or "indefinido"
    st.markdown(f"**Padroes detectados:** {detected}")
    st.markdown(f"**Perfil de valor (ultimas {analysis_window}):** altas {value_profile['count_high']}, medias {value_profile['count_med']}, baixas {value_profile['count_low']}, avg {value_profile['avg_value']:.1f}")
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

# ========== LAST PLAYS TABLE ==========
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
    txt += f"Sugestao: {suggestion['text']}\n"
    txt += f"Probabilidades: RED {probs['red']}%, BLUE {probs['blue']}%, TIE {probs['tie']}%\n"
    txt += f"Confianca: {probs['confidence']}%\n\n"
    txt += "Ultimas 30 jogadas:\n"
    txt += analysis_df.tail(30).to_csv(index=False)
    st.download_button("Baixar relatorio (TXT)", data=txt, file_name="relatorio_football_studio.txt")

st.caption("Analise hibrida: valor das cartas + padrao de cores. Probabilidades sao estimativas; aposte com responsabilidade.")
