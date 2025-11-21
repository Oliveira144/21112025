football_studio_analisador_pro.py

Football Studio Analyzer - Profissional Completo

App único (Streamlit) com:

- Força real das cartas e peso dinâmico

- Leitura de padrões combinados (repetição, alternância, degrau, quebra, ciclos)

- Nível de manipulação (1-9)

- Detector de quebra (pontuação 0–100)

- Probabilidades ponderadas RED/BLUE/TIE

- Sugestão de aposta profissional (regra OU–OU: se quebra >=50% -> NÃO APOSTAR)

- Inserção rápida com botões coloridos por carta

- Histórico detalhado, export CSV/TXT

import streamlit as st import pandas as pd import numpy as np from datetime import datetime

st.set_page_config(page_title="Football Studio Analyzer - Profissional Completo", layout="wide")

----------------------------- Configuração / Constantes -----------------------------

CARD_MAP = {"A":14, "K":13, "Q":12, "J":11, "10":10, "9":9, "8":8, "7":7, "6":6, "5":5, "4":4, "3":3, "2":2}

Classes por regra comum (usar para análise qualitativa)

HIGH = {"A","K","Q","J"} MEDIUM = {"10","9","8"} LOW = {"7","6","5","4","3","2"}

Força usada em heurísticas (1..5)

CARD_STRENGTH = {"A":5, "K":5, "Q":5, "J":4, "10":4, "9":3, "8":3, "7":2, "6":1, "5":1, "4":1, "3":1, "2":1}

CARD_ORDER = ["A","K","Q","J","10","9","8","7","6","5","4","3","2"] MAX_COLS = 9 MAX_LINES = 10

----------------------------- Utilitários -----------------------------

def card_value(label: str) -> int: return CARD_MAP.get(str(label), 0)

def card_group(label: str) -> str: if label in HIGH: return "alta" if label in MEDIUM: return "media" if label in LOW: return "baixa" return "tie"

def strength_of(label: str) -> int: return CARD_STRENGTH.get(label, 1)

----------------------------- Estado (session) -----------------------------

if "history" not in st.session_state: # columns: timestamp, winner, card, value, value_class, strength st.session_state.history = pd.DataFrame(columns=["timestamp","winner","card","value","value_class","strength"])

----------------------------- Funções de manipulação do histórico -----------------------------

def add_result(winner: str, card_label: str): now = datetime.now() if card_label == "T": v = 0 vc = "tie" s = 0 else: v = card_value(card_label) vc = card_group(card_label) s = strength_of(card_label) new_row = pd.DataFrame([{"timestamp": now, "winner": winner, "card": card_label, "value": v, "value_class": vc, "strength": s}]) st.session_state.history = pd.concat([st.session_state.history, new_row], ignore_index=True)

def reset_history(): st.session_state.history = pd.DataFrame(columns=["timestamp","winner","card","value","value_class","strength"])

----------------------------- Sidebar / Configurações -----------------------------

with st.sidebar: st.header("Controles") if st.button("Resetar Histórico"): reset_history() st.write("---") st.markdown("Exportar / Configurações") csv_data = st.session_state.history.to_csv(index=False) st.download_button("Exportar histórico (CSV)", data=csv_data, file_name="history_football_studio.csv") st.write("---") show_timestamps = st.checkbox("Mostrar timestamps", value=False) show_confidence_bar = st.checkbox("Mostrar barra de confiança", value=True) st.markdown("Janela móvel para análise (últimas N jogadas)") analysis_window = st.selectbox("Últimas N", options=[3,5,8,10,20,50], index=3)

----------------------------- Inserção rápida com botões coloridos -----------------------------

st.title("Football Studio Analyzer — Profissional Completo") st.markdown("Use os botões abaixo para inserir rapidamente o resultado (1 clique por carta).")

col_red, col_blue, col_tie = st.columns(3) with col_red: st.markdown("<div style='text-align:center; color:#b30000; font-weight:bold;'>🔴 RED</div>", unsafe_allow_html=True) for card in CARD_ORDER: if st.button(card, key=f"red_{card}"): add_result("red", card) with col_blue: st.markdown("<div style='text-align:center; color:#1f4fff; font-weight:bold;'>🔵 BLUE</div>", unsafe_allow_html=True) for card in CARD_ORDER: if st.button(card, key=f"blue_{card}"): add_result("blue", card) with col_tie: st.markdown("<div style='text-align:center; color:#c7a400; font-weight:bold;'>🟡 TIE</div>", unsafe_allow_html=True) if st.button("TIE", key="tie_main"): add_result("tie", "T")

st.write("---")

----------------------------- Histórico (visualização em grade) -----------------------------

st.subheader("Histórico (últimas inserções)") history = st.session_state.history.copy() if len(history) > MAX_COLS * MAX_LINES: history = history.tail(MAX_COLS * MAX_LINES).reset_index(drop=True)

if history.empty: st.info("Sem resultados ainda. Use os botões acima para inserir resultados.") else: rows = [history.iloc[i:i+MAX_COLS] for i in range(0, len(history), MAX_COLS)] for row_df in rows: cols = st.columns(MAX_COLS) for c_idx in range(MAX_COLS): with cols[c_idx]: if c_idx < len(row_df): item = row_df.iloc[c_idx] if item['winner'] == 'red': label = f"🔴 {item['card']} ({item['value_class']})" elif item['winner'] == 'blue': label = f"🔵 {item['card']} ({item['value_class']})" else: label = f"🟡 TIE" if show_timestamps: st.caption(str(item['timestamp'])) st.markdown(f"{label}") else: st.write("")

----------------------------- Padrões e Heurísticas Profissionais -----------------------------

def detect_patterns(df: pd.DataFrame) -> dict: patterns = {"repeticao": False, "alternancia": False, "degrau": False, "quebra_controlada": False, "ciclo": False} if df.empty: return patterns winners = df['winner'].tolist() classes = df['value_class'].tolist() n = len(df) # repetição: últimos 3 iguais (exceto tie) if n >= 3 and winners[-1] == winners[-2] == winners[-3] and winners[-1] != 'tie': patterns['repeticao'] = True # alternância: ABAB últimos 4 if n >= 4 and winners[-1] == winners[-3] and winners[-2] == winners[-4] and winners[-1] != winners[-2]: patterns['alternancia'] = True # degrau: A A B B A A if n >= 6: seq = winners[-6:] if seq[0] == seq[1] and seq[2] == seq[3] and seq[4] == seq[5] and seq[0] == seq[4]: patterns['degrau'] = True # quebra controlada: baixa, baixa, alta últimas 3 classes if n >= 3: if classes[-3] == 'baixa' and classes[-2] == 'baixa' and classes[-1] == 'alta': patterns['quebra_controlada'] = True # ciclo simples: repetição de bloco if n >= 10: last10 = winners[-10:] if last10[:5] == last10[5:]: patterns['ciclo'] = True return patterns

def compute_manipulation_level(df: pd.DataFrame) -> int: if df.empty: return 1 vals = df['value_class'].tolist() winners = df['winner'].tolist() n = len(df) score = 0.0 # runs of low values low_run = 0 low_runs_count = 0 for v in vals: if v == 'baixa': low_run += 1 else: if low_run >= 2: low_runs_count += 1 low_run = 0 if low_run >= 2: low_runs_count += 1 score += low_runs_count * 1.5 # alternation rate alternations = sum(1 for i in range(1, n) if winners[i] != winners[i-1]) score += (alternations / max(1, n-1)) * 3.0 # many highs reduce suspicion high_count = sum(1 for v in vals if v == 'alta') score -= (high_count / n) * 1.5 # ties increase suspicion tie_count = sum(1 for w in winners if w == 'tie') score += (tie_count / n) * 2.0 lvl = int(min(9, max(1, round(score)))) return lvl

def detect_break_score(df: pd.DataFrame) -> dict: if df.empty: return {"break_score": 0, "reason": ""} classes = df['value_class'].tolist() winners = df['winner'].tolist() n = len(df) score = 0 reasons = [] recent = classes[-5:] low_count = sum(1 for x in recent if x == 'baixa') score += low_count * 15 if low_count >= 3: reasons.append(f"{low_count}/5 baixas recentes") if classes[-1] == 'baixa': score += 15 reasons.append("Última carta baixa") recent_winners = winners[-6:] if n >= 6 else winners alt = sum(1 for i in range(1, len(recent_winners)) if recent_winners[i] != recent_winners[i-1]) if len(recent_winners) > 1 and (alt / (len(recent_winners)-1)) >= 0.75: score += 20 reasons.append("Alternância acelerada") # ties influence tie_recent = winners[-5:].count('tie') if tie_recent >= 1: score += tie_recent * 5 reasons.append(f"{tie_recent} ties recentes") score = min(100, score) return {"break_score": score, "reason": "; ".join(reasons)}

def weighted_probs(df: pd.DataFrame, window: int = 10) -> dict: if df.empty: return {"red":49.0, "blue":49.0, "tie":2.0, "confidence":0.0} sub = df.tail(window).reset_index(drop=True) m = len(sub) weights = np.linspace(1, 0.2, m) weights = weights / weights.sum() score = {"red":0.0, "blue":0.0, "tie":0.0} for i, row in sub.iterrows(): w = weights[i] winner = row['winner'] if row['card'] == 'T': factor = 0.6 else: factor = strength_of(row['card']) / 5.0 if winner == 'red': score['red'] += w * (0.6 + 0.4 * factor) elif winner == 'blue': score['blue'] += w * (0.6 + 0.4 * factor) else: score['tie'] += w * (0.5 + 0.5 * (1 - factor)) # smooth score['red'] += 1e-9 score['blue'] += 1e-9 score['tie'] += 1e-9 total = score['red'] + score['blue'] + score['tie'] probs = {k: round((v/total)*100,1) for k,v in score.items()} values = np.array(list(score.values())) peakness = values.max()/values.sum() confidence = min(0.99, max(0.05, peakness)) * 100 return {"red": probs['red'], "blue": probs['blue'], "tie": probs['tie'], "confidence": round(confidence,1)}

def make_suggestion(probs: dict, break_info: dict, manip_level: int) -> dict: """Regra OU-OU: se break_score >=50 => NÃO APOSTAR; caso contrário sugerir baseada em probs e confiança.""" break_score = break_info.get('break_score', 0) reason = break_info.get('reason', '') # If break strong -> do NOT suggest color if break_score >= 50: return {"action": "no_bet", "text": f"NÃO APOSTAR — quebra provável ({break_score}%)", "reason": reason, "confidence": break_score} # otherwise choose top if probs['tie'] >= 12: return {"action":"bet_tie", "text": "Apostar TIE (🟡)", "reason": reason, "confidence": probs['confidence']} top_color = 'red' if probs['red'] > probs['blue'] else 'blue' if probs[top_color] >= 60 or probs['confidence'] >= 70: emoji = '🔴' if top_color=='red' else '🔵' return {"action":"bet_color", "text": f"Apostar {top_color.upper()} ({emoji})", "reason": reason, "confidence": probs['confidence']} return {"action":"wait", "text":"Aguardar (sem entrada segura)", "reason": reason, "confidence": probs['confidence']}

----------------------------- Execução da Análise -----------------------------

st.subheader("Análise e Previsão") analysis_df = st.session_state.history.copy() patterns = detect_patterns(analysis_df) manip_level = compute_manipulation_level(analysis_df) break_info = detect_break_score(analysis_df) probs = weighted_probs(analysis_df, window=analysis_window) suggestion = make_suggestion(probs, break_info, manip_level)

Display: separate suggestion from break warning clearly

colA, colB = st.columns([2,1]) with colA: st.markdown(f"Padrões detectados: {', '.join([k for k,v in patterns.items() if v]) or 'indefinido'}") st.markdown(f"Nível de manipulação (1–9): {manip_level}") # Suggestion block if suggestion['action'] == 'no_bet': st.error(f"⚠️ {suggestion['text']}") if suggestion['reason']: st.write(f"Motivos: {suggestion['reason']}") st.write(f"Confiança (break): {suggestion['confidence']} %") elif suggestion['action'] == 'bet_tie': st.success(suggestion['text']) st.write(f"Confiança: {suggestion['confidence']} %") elif suggestion['action'] == 'bet_color': st.success(suggestion['text']) st.write(f"Confiança: {suggestion['confidence']} %") else: st.info(suggestion['text']) st.write(f"Confiança: {suggestion['confidence']} %") # show reasons if break present but below threshold if break_info['break_score'] > 0 and suggestion['action'] != 'no_bet': st.warning(f"Alerta (break score {break_info['break_score']}%): {break_info['reason']}")

with colB: st.metric("🔴 RED", f"{probs['red']} %") st.metric("🔵 BLUE", f"{probs['blue']} %") st.metric("🟡 TIE", f"{probs['tie']} %")

if show_confidence_bar: st.progress(int(min(100, probs['confidence'])))

st.markdown("---")

----------------------------- Últimas jogadas e interpretação -----------------------------

st.subheader("Resumo das últimas jogadas (últimas 30)") st.dataframe(analysis_df.tail(30).reset_index(drop=True))

st.markdown("Interpretação (por valor da carta):") st.markdown("- Cartas A, K, Q, J: consideradas ALTAS. Vitória com alta tende a repetir.

Cartas 10, 9, 8: consideradas MÉDIAS. Zona de transição — observe sinais.

Cartas 7–2: consideradas BAIXAS. Alta probabilidade de quebra — evite manter a cor.")


st.markdown("Estratégia operacional (resumo):") st.markdown("1. Use janela móvel e confirme padrão. 2. Se BREAK >= 50% → NÃO APOSTAR. 3. Se não houver break, entre somente se prob >= 60% ou confiança >= 70%. 4. Gerencie banca: stake baixo em sinais incertos. 5. Empates (TIE) aumentam suspeita; trate como âncora de manipulação.")

----------------------------- Ferramentas / Export -----------------------------

st.markdown("---") st.header("Ferramentas")

if st.button("Gerar relatório (TXT)"): now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") txt = f"Football Studio Analyzer - Relatório Profissional Gerado em: {now} " txt += f"Padrões detectados: {', '.join([k for k,v in patterns.items() if v]) or 'indefinido'} " txt += f"Nível de manipulação: {manip_level} " if suggestion['action'] == 'no_bet': txt += f"RECOMENDAÇÃO: NÃO APOSTAR — quebra provável ({break_info['break_score']}%) " if break_info['reason']: txt += f"Motivos: {break_info['reason']} " else: txt += f"RECOMENDAÇÃO: {suggestion['text']} " txt += f"Probabilidades: RED {probs['red']}%, BLUE {probs['blue']}%, TIE {probs['tie']}% " txt += f"Confiança: {probs['confidence']}% " txt += " Últimas 30 jogadas: " txt += analysis_df.tail(30).to_csv(index=False) st.download_button("Baixar relatório (TXT)", data=txt, file_name="relatorio_football_studio.txt")

st.markdown("---") st.caption("Sistema profissional. Probabilidades são estimativas; aposte com responsabilidade.")
