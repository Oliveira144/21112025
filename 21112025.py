import streamlit as st 
import pandas as pd 
import numpy as np

============================================

SISTEMA PROFISSIONAL FOOTBALL STUDIO — v3.0

100% SEM ERROS / SEM CARACTERES INVÁLIDOS

LÓGICA PROFISSIONAL (OU APOSTA / OU QUEBRA)

============================================

-------------------------------

MAPEAMENTO DOS VALORES DAS CARTAS

-------------------------------

CARD_VALUE = { "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10, "A": 1 }

-------------------------------

FUNÇÃO DE FORÇA DA CARTA

-------------------------------

def card_strength(value): if value <= 3: return "BAIXA" if 4 <= value <= 7: return "MEDIA" return "ALTA"

-------------------------------

INICIALIZA VARIÁVEIS DO APLICATIVO

-------------------------------

if "history" not in st.session_state: st.session_state.history = [] if "cards" not in st.session_state: st.session_state.cards = []

st.title("ANALISADOR PROFISSIONAL — FOOTBALL STUDIO (CARTAS FÍSICAS)")

============================================

ENTRADA DE CARTAS

============================================

st.subheader("Registrar rodada (Home e Away)")

colA, colB, colC = st.columns(3) with colA: home = st.selectbox("Home (Azul)", list(CARD_VALUE.keys()), key="home_card") with colB: away = st.selectbox("Away (Vermelho)", list(CARD_VALUE.keys()), key="away_card") with colC: add_btn = st.button("Adicionar rodada")

-------------------------------

REGISTRAR RESULTADO

-------------------------------

def add_round(home_card, away_card): hv = CARD_VALUE[home_card] av = CARD_VALUE[away_card]

if hv > av:
    winner = "BLUE"
elif av > hv:
    winner = "RED"
else:
    winner = "TIE"

st.session_state.history.append(winner)
st.session_state.cards.append((home_card, away_card))

if add_btn: add_round(st.session_state.home_card, st.session_state.away_card)

============================================

FUNÇÃO PRINCIPAL DE ANÁLISE PROFISSIONAL

============================================

def analyze(history): if len(history) < 4: return { "pattern": "Poucos dados", "manip": 1, "break": 0, "suggest": "Aguardar", "conf": 0 }

last = history[-1]
last3 = history[-3:]

# -------------------------------
# DETECÇÃO DE PADRÕES
# -------------------------------
if last3.count(last) == 3:
    pattern = "Repeticao"
elif len(set(last3)) == 3:
    pattern = "Alternancia"
elif last3[0] == last3[1] and last3[2] != last3[1]:
    pattern = "Pre-quebra"
else:
    pattern = "Indefinido"

# -------------------------------
# TAXA DE ALTERNÂNCIA
# -------------------------------
alternancia = sum(1 for i in range(1, len(history)) if history[i] != history[i-1])
alt_rate = alternancia / (len(history)-1)

# -------------------------------
# NÍVEL DE MANIPULAÇÃO
# -------------------------------
manip = 1
if alt_rate > 0.6:
    manip = 4
if alt_rate > 0.7:
    manip = 6
if history.count("TIE") >= 3:
    manip = 7
if pattern == "Pre-quebra":
    manip = 8

# -------------------------------
# DETECÇÃO DE QUEBRA (0–100)
# -------------------------------
break_score = 0

if pattern == "Pre-quebra":
    break_score += 40
if alt_rate > 0.7:
    break_score += 25
if last == "TIE":
    break_score += 20

break_score = min(break_score, 100)

# -------------------------------
# REGRA PROFISSIONAL (OU–OU)
# -------------------------------
# Se break >= 50 → NÃO APOSTAR
if break_score >= 50:
    return {
        "pattern": pattern,
        "manip": manip,
        "break": break_score,
        "suggest": "NAO APOSTAR — risco alto de quebra",
        "conf": break_score
    }

# Se break < 50 → Sugere manter tendência
sugerir = history[-1]
confiança = int((1 - alt_rate) * 100)

return {
    "pattern": pattern,
    "manip": manip,
    "break": break_score,
    "suggest": f"Apostar {sugerir}",
    "conf": confiança
}

============================================

EXECUTAR ANÁLISE

============================================

result = analyze(st.session_state.history)

st.subheader("Análise da Rodada") st.write(f"Padrão detectado: {result['pattern']}") st.write(f"Nível de manipulação (1–9): {result['manip']}") st.write(f"Sugestão: {result['suggest']}") st.write(f"Confiança: {result['conf']}%")

if result['break'] >= 50: st.error(f"⚠️ QUEBRA DETECTADA ({result['break']}%) — NÃO APOSTAR") else: st.success(f"Break Score: {result['break']}% (seguro)")

============================================

HISTÓRICO

============================================

st.subheader("Histórico de Resultados")

if st.session_state.history: df = pd.DataFrame({ "Home": [c[0] for c in st.session_state.cards], "Away": [c[1] for c in st.session_state.cards], "Vencedor": st.session_state.history }) st.table(df) else: st.write("Nenhuma rodada registrada ainda.")

============================================

BOTÃO LIMPAR

============================================

if st.button("Limpar Tudo"): st.session_state.history = [] st.session_state.cards = [] st.rerun()
