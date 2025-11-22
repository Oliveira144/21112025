# app.py (VERSÃO CORRIGIDA: filtra só rodadas completas + sugestão sem contradição)
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ========= Config =========
st.set_page_config(page_title="Football Studio Pro - Corrigido", layout="wide")
st.title("Football Studio Pro — Corrigido (Análise só com rodadas completas)")

# ========= Constantes =========
CARD_ORDER = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
CARD_MAP = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"10":10,"J":11,"Q":12,"K":13,"A":14}
HIGH = {"A","K","Q","J"}
MEDIUM = {"10","9","8"}
LOW = {"7","6","5","4","3","2"}
CARD_STRENGTH = {"A":5,"K":5,"Q":5,"J":4,"10":4,"9":3,"8":3,"7":2,"6":1,"5":1,"4":1,"3":1,"2":1}
MAX_DISPLAY = 90

# ========= Estado =========
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        "timestamp","winner","home_card","away_card",
        "home_value","away_value","home_class","away_class",
        "home_strength","away_strength"
    ])
if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = []
if "sel_home" not in st.session_state:
    st.session_state.sel_home = None
if "sel_away" not in st.session_state:
    st.session_state.sel_away = None

# ========= Sidebar =========
with st.sidebar:
    st.header("Configurações")
    if st.button("Resetar histórico"):
        st.session_state.undo_stack.append(st.session_state.history.copy())
        st.session_state.history = st.session_state.history.iloc[0:0]
        st.session_state.sel_home = None
        st.session_state.sel_away = None
        st.success("Histórico resetado.")
    st.write("---")
    st.download_button("Exportar histórico (CSV)", data=st.session_state.history.to_csv(index=False), file_name="history.csv")
    show_timestamps = st.checkbox("Mostrar timestamps", value=False)
    show_confidence_bar = st.checkbox("Mostrar barra de confiança", value=True)
    analysis_window = st.selectbox("Janela de análise (últimas N rodadas completas)", options=[3,5,8,10,20,50], index=3)
    break_threshold = st.slider("Limite de break (%) que bloqueia aposta", 30, 80, 50, 5)
    aggressive_override = st.checkbox("Override agressivo (ignorar block de break e sugerir com aviso)", value=False)
    st.caption("Home = 🔴 Vermelho (CASA). Visitante = 🔵 Azul (AWAY).")

# ========= Helpers =========
def normalize(card):
    return str(card).strip().upper()

def card_value(card):
    return CARD_MAP.get(normalize(card), 0)

def card_class(card):
    c = normalize(card)
    if c in HIGH: return "alta"
    if c in MEDIUM: return "media"
    if c in LOW: return "baixa"
    return "tie"

def card_strength(card):
    return CARD_STRENGTH.get(normalize(card), 0)

def push_undo():
    st.session_state.undo_stack.append(st.session_state.history.copy())

def append_round(home_card, away_card):
    now = datetime.now()
    hc = normalize(home_card); ac = normalize(away_card)
    hv = card_value(hc); av = card_value(ac)
    hc_class = card_class(hc); ac_class = card_class(ac)
    hs = card_strength(hc); as_ = card_strength(ac)
    if hv > av:
        winner = "RED"
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
    st.session_state.sel_home = None
    st.session_state.sel_away = None

# ========= Input (horizontal compact) =========
st.subheader("Inserção rápida — escolha CASA (🔴) + VISITANTE (🔵). Registro só conta na análise quando AMBAS as cartas existirem.")
st.markdown("Clique numa carta para selecionar; quando selecionar os dois lados a rodada é gravada automaticamente.")

# CASA (RED)
st.markdown("**🔴 CASA (VERMELHO)**")
cols_home = st.columns(len(CARD_ORDER))
for i, val in enumerate(CARD_ORDER):
    with cols_home[i]:
        if st.button(val, key=f"home_{val}"):
            st.session_state.sel_home = val
            # se away já selecionada -> grava
            if st.session_state.sel_away:
                append_round(st.session_state.sel_home, st.session_state.sel_away)
                st.success(f"Rodada gravada: CASA {st.session_state.sel_home} vs VISITANTE {st.session_state.sel_away}")
            else:
                st.info(f"Selecionado CASA {val} — selecione VISITANTE para gravar")

# AWAY (BLUE)
st.markdown("**🔵 VISITANTE (AZUL)**")
cols_away = st.columns(len(CARD_ORDER))
for i, val in enumerate(CARD_ORDER):
    with cols_away[i]:
        if st.button(val, key=f"away_{val}"):
            st.session_state.sel_away = val
            if st.session_state.sel_home:
                append_round(st.session_state.sel_home, st.session_state.sel_away)
                st.success(f"Rodada gravada: CASA {st.session_state.sel_home} vs VISITANTE {st.session_state.sel_away}")
            else:
                st.info(f"Selecionado VISITANTE {val} — selecione CASA para gravar")

# quick add one-click
st.markdown("---")
st.subheader("Adicionar rodada em 1 clique (opcional)")
c1,c2,c3 = st.columns([3,3,2])
with c1:
    quick_home = st.selectbox("Casa (VERMELHO)", CARD_ORDER, key="qhome")
with c2:
    quick_away = st.selectbox("Visitante (AZUL)", CARD_ORDER, key="qaway")
with c3:
    if st.button("Adicionar (1 clique)"):
        append_round(quick_home, quick_away)
        st.success(f"Rodada adicionada: CASA {quick_home} vs VISITANTE {quick_away}")

# undo/clear
st.markdown("---")
cundo, cclr = st.columns([1,1])
with cundo:
    if st.button("Desfazer ultima"):
        if st.session_state.undo_stack:
            st.session_state.history = st.session_state.undo_stack.pop()
            st.success("Desfeito.")
        else:
            st.warning("Nada para desfazer.")
with cclr:
    if st.button("Limpar tudo"):
        st.session_state.undo_stack.append(st.session_state.history.copy())
        st.session_state.history = st.session_state.history.iloc[0:0]
        st.session_state.sel_home = None; st.session_state.sel_away = None
        st.success("Limpo.")

# ========= Display histórico (visível) =========
st.markdown("---")
st.subheader("Histórico (visual) — últimas entradas (provisórias aparecem mas não contam na análise)")
hist = st.session_state.history.copy()
if hist.empty:
    st.info("Sem rodadas gravadas ainda.")
else:
    display = hist.tail(MAX_DISPLAY).reset_index(drop=True)
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

# =========** CRUCIAL FIX **=========
# For analysis we MUST use only complete rows (both cards present).
complete_df = st.session_state.history.dropna(subset=["home_card","away_card"]).copy().reset_index(drop=True)

# ========= Analysis functions (same as before, but operate on complete_df) =========
def detect_patterns(df):
    patterns = {"repeticao": False, "alternancia": False, "degrau": False, "quebra_controlada": False, "ciclo": False}
    if df.empty: return patterns
    winners = df["winner"].tolist()
    classes = []
    for i,row in df.iterrows():
        if row["winner"] == "RED": classes.append(row["home_class"])
        elif row["winner"] == "BLUE": classes.append(row["away_class"])
        else: classes.append("tie")
    n = len(winners)
    if n>=3 and winners[-1]==winners[-2]==winners[-3] and winners[-1]!="TIE": patterns["repeticao"]=True
    if n>=4 and winners[-1]==winners[-3] and winners[-2]==winners[-4] and winners[-1]!=winners[-2]: patterns["alternancia"]=True
    if n>=6:
        seq = winners[-6:]
        if seq[0]==seq[1] and seq[2]==seq[3] and seq[4]==seq[5] and seq[0]==seq[4]: patterns["degrau"]=True
    if n>=3 and classes[-3]=="baixa" and classes[-2]=="baixa" and classes[-1]=="alta": patterns["quebra_controlada"]=True
    if n>=10:
        last10=winners[-10:]
        if last10[:5]==last10[5:]: patterns["ciclo"]=True
    return patterns

def compute_value_profile(df, window=10):
    if df.empty: return {"n":0,"count_high":0,"count_med":0,"count_low":0,"avg_value":0.0,"high_ratio":0.0}
    sub = df.tail(window)
    n=len(sub); ch=cm=cl=0; vals=[]
    for _,row in sub.iterrows():
        # use winner card as primary indicator
        if row["winner"]=="RED": cls=row["home_class"]; val=row["home_value"]
        elif row["winner"]=="BLUE": cls=row["away_class"]; val=row["away_value"]
        else: cls="tie"; val=max(row["home_value"], row["away_value"])
        vals.append(val)
        if cls=="alta": ch+=1
        elif cls=="media": cm+=1
        elif cls=="baixa": cl+=1
    avg = float(np.mean(vals)) if vals else 0.0
    return {"n":n,"count_high":ch,"count_med":cm,"count_low":cl,"avg_value":avg,"high_ratio": ch/n if n>0 else 0.0}

def detect_break_score(df):
    if df.empty: return {"break_score":0,"reason":""}
    score=0; reasons=[]
    vp5 = compute_value_profile(df, window=5)
    if vp5["count_low"]>=3: score+=20; reasons.append(f"{vp5['count_low']}/5 cartas baixas vencedoras")
    last = df.iloc[-1]
    last_class = last["home_class"] if last["winner"]=="RED" else (last["away_class"] if last["winner"]=="BLUE" else "tie")
    if last_class=="baixa": score+=15; reasons.append("Última vencedora baixa")
    recent = df["winner"].tolist()[-6:] if len(df)>=6 else df["winner"].tolist()
    if len(recent)>1:
        alt = sum(1 for i in range(1,len(recent)) if recent[i]!=recent[i-1])
        if (alt/(len(recent)-1))>=0.75:
            score+=25; reasons.append("Alternância acelerada")
    ties = df["winner"].tolist()[-6:].count("TIE")
    if ties>=1: score+=ties*5; reasons.append(f"{ties} ties recentes")
    vp10 = compute_value_profile(df, window=10)
    if vp10["count_high"]>=4: score-=10; reasons.append("Muitas altas recentes (reduz risco)")
    score = int(max(0,min(100,score)))
    return {"break_score":score,"reason":"; ".join(reasons)}

def weighted_probs(df, window=10):
    if df.empty:
        return {"red":49.0,"blue":49.0,"tie":2.0,"confidence":0.0}
    sub = df.tail(window).reset_index(drop=True)
    m=len(sub); weights = np.linspace(1.0,0.2,m); weights = weights/weights.sum()
    scr={"red":0.0,"blue":0.0,"tie":0.0}
    for i,row in sub.iterrows():
        w = weights[i]
        if row["winner"]=="RED":
            factor = CARD_STRENGTH.get(row["home_card"],1)/5.0
            scr["red"] += w*(0.6+0.4*factor)
        elif row["winner"]=="BLUE":
            factor = CARD_STRENGTH.get(row["away_card"],1)/5.0
            scr["blue"] += w*(0.6+0.4*factor)
        else:
            factor=0.6
            scr["tie"] += w*(0.5+0.5*(1-factor))
    for k in scr: scr[k]+=1e-9
    total = scr["red"]+scr["blue"]+scr["tie"]
    probs = {k: round((v/total)*100,1) for k,v in scr.items()}
    values = np.array(list(scr.values())); peakness = values.max()/values.sum()
    confidence = float(round(min(0.99, max(0.05, peakness))*100,1))
    probs["confidence"]=confidence
    return probs

def compute_manipulation_level(df):
    if df.empty: return 1
    winners = df["winner"].tolist(); n=len(winners)
    vals=[]
    for _,row in df.iterrows():
        if row["winner"]=="RED": vals.append(row["home_class"])
        elif row["winner"]=="BLUE": vals.append(row["away_class"])
        else: vals.append("tie")
    score=0.0; low_run=0; low_runs=0
    for v in vals:
        if v=="baixa": low_run+=1
        else:
            if low_run>=2: low_runs+=1
            low_run=0
    if low_run>=2: low_runs+=1
    score += low_runs*1.5
    alternations = sum(1 for i in range(1,n) if winners[i]!=winners[i-1])
    score += (alternations/max(1,n-1))*3.0
    high_count = sum(1 for v in vals if v=="alta")
    score -= (high_count/n)*1.5
    tie_count = winners.count("TIE"); score += (tie_count/n)*2.0
    lvl = int(min(9, max(1, round(score))))
    return lvl

def make_suggestion(df, window=10):
    # operate only on df (complete rounds)
    if df.empty:
        return {"action":"wait","text":"AGUARDAR - sem rodadas completas","probs":{"red":49.0,"blue":49.0,"tie":2.0,"confidence":0.0},"break_score":0}
    probs = weighted_probs(df, window=window)
    break_info = detect_break_score(df)
    break_score = break_info["break_score"]
    patterns = detect_patterns(df)
    manip = compute_manipulation_level(df)
    any_pattern = any(patterns.values())
    top_color = "RED" if probs["red"]>probs["blue"] else "BLUE"
    top_prob = probs["red"] if top_color=="RED" else probs["blue"]
    conf = probs["confidence"]
    # tie case
    if probs["tie"] >= 12.0:
        return {"action":"bet_tie","text":f"APOSTAR TIE (🟡) - prob {probs['tie']}%","probs":probs,"break_score":break_score}
    # default blocking rule
    if break_score >= break_threshold:
        # block suggestion unless aggressive_override True
        if aggressive_override:
            emoji = "🔴" if top_color=="RED" else "🔵"
            txt = f"APOSTAR {top_color} ({emoji}) - prob {top_prob}% / conf {conf}%  ⚠ BREAK {break_score}% (OVERRIDE)"
            return {"action":"bet_color_override","text":txt,"probs":probs,"break_score":break_score}
        else:
            return {"action":"no_bet","text":f"NAO APOSTAR - quebra provavel ({break_score}%)","probs":probs,"break_score":break_score}
    # aggressive behavior: suggest when any pattern OR top_prob >=55 OR conf>=50
    if any_pattern or top_prob>=55.0 or conf>=50.0:
        emoji = "🔴" if top_color=="RED" else "🔵"
        txt = f"APOSTAR {top_color} ({emoji}) - prob {top_prob}% / conf {conf}%"
        return {"action":"bet_color","text":txt,"probs":probs,"break_score":break_score}
    return {"action":"wait","text":"AGUARDAR - sem entrada segura","probs":probs,"break_score":break_score}

# ========= Run analysis & display =========
st.markdown("---")
st.subheader("Analise e Previsao (apenas rodadas completas entram na analise)")

# use complete_df for all analysis
complete_df = complete_df  # already defined above
patterns = detect_patterns(complete_df)
value_profile = compute_value_profile(complete_df, window=analysis_window)
break_info = detect_break_score(complete_df)
probs = weighted_probs(complete_df, window=analysis_window)
manip_level = compute_manipulation_level(complete_df)
suggestion = make_suggestion(complete_df, window=analysis_window)

colA, colB = st.columns([2,1])
with colA:
    detected = ", ".join([k for k,v in patterns.items() if v]) or "indefinido"
    st.markdown(f"**Padroes detectados (rodadas completas):** {detected}")
    st.markdown(f"**Perfil de valor (ultimas {analysis_window}):** altas {value_profile['count_high']}, medias {value_profile['count_med']}, baixas {value_profile['count_low']}, avg {value_profile['avg_value']:.1f}")
    st.markdown(f"**Nivel de manipulacao (1-9):** {manip_level}")
    st.markdown(f"**Break score:** {break_info['break_score']}%")
    if break_info["reason"]: st.write(f"Motivos: {break_info['reason']}")
    st.markdown(f"**Sugestao:** {suggestion['text']}")
    # Explicit: show how many rounds were used
    st.info(f"Rodadas completas usadas na analise: {len(complete_df)} (de {len(st.session_state.history)} registradas)")
with colB:
    st.metric("🔴 RED (CASA)", f"{probs['red']} %")
    st.metric("🔵 BLUE (VISITANTE)", f"{probs['blue']} %")
    st.metric("🟡 TIE", f"{probs['tie']} %")
    if show_confidence_bar: st.progress(int(min(100, probs["confidence"])))

st.markdown("---")
st.subheader("Resumo (ultimas 30 rodadas completas)")
if complete_df.empty:
    st.info("Nenhuma rodada completa para exibir.")
else:
    st.dataframe(complete_df.tail(30).reset_index(drop=True))

# ========= Tools =========
st.markdown("---")
st.header("Ferramentas")
st.download_button("Exportar historico completo (CSV)", data=st.session_state.history.to_csv(index=False), file_name="history_full.csv")

if st.button("Gerar relatorio (TXT)"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    detected_list = ", ".join([k for k,v in patterns.items() if v]) or "indefinido"
    txt = f"Football Studio - Relatorio\nGerado: {now}\nPadroes: {detected_list}\nBreak score: {break_info['break_score']}% - {break_info['reason']}\nNivel manipulacao: {manip_level}\nSugestao: {suggestion['text']}\nProbabilidades: RED {probs['red']}%, BLUE {probs['blue']}%, TIE {probs['tie']}%\nConf: {probs['confidence']}%\n\nUltimas 30 rodadas completas:\n"
    txt += complete_df.tail(30).to_csv(index=False)
    st.download_button("Baixar relatorio (TXT)", data=txt, file_name="relatorio.txt")

st.caption("Nota: análise usa apenas rodadas completas (home+away). Se desejar que provisórias também contem, avise — mas isso prejudica precisão.")
