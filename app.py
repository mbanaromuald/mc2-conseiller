import io, streamlit as st, pandas as pd
from gtts import gTTS
import agents as A, data as D

st.set_page_config(page_title="Conseiller MC2 · SAPA", page_icon=":material/agriculture:", layout="centered")

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,800&family=Manrope:wght@400;600;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"], .stApp {font-family:'Manrope',system-ui,sans-serif;}
.stApp {background:radial-gradient(1200px 500px at 50% -10%, #1F4A31 0%, #0D2318 60%);}
.stApp::before {content:"";position:fixed;top:0;left:0;right:0;height:5px;z-index:99;
  background:linear-gradient(90deg,#0A7C3E 33%,#CE1126 33% 66%,#FCD116 66%);}
.block-container {max-width:760px;padding-top:2.2rem;}
h1,h2,h3 {font-family:'Fraunces',serif !important;letter-spacing:-.01em;}
.hero {padding:1.6rem 0 .6rem;}
.hero .org {color:#E9B824;font-weight:700;font-size:.95rem;margin-bottom:.6rem;}
.hero h1 {font-size:2.7rem;line-height:1.05;font-weight:800;margin:0 0 .8rem;}
.hero p {font-size:1.08rem;line-height:1.55;color:#D9D3BD;max-width:34rem;}
.trio {display:flex;gap:.6rem;flex-wrap:wrap;margin:1rem 0 .4rem;}
.trio span {background:#143223;border:1px solid #2C5A3F;border-radius:999px;padding:.4rem .9rem;font-size:.88rem;color:#F4EFDF;}
.stButton>button, .stDownloadButton>button {border-radius:16px;padding:.7rem 1.2rem;font-weight:700;width:100%;
  background:#E9B824;color:#0D2318;border:0;}
.stButton>button:hover {background:#F5CB47;color:#0D2318;}
[data-testid="stChatMessage"] {background:#143223;border:1px solid #2C5A3F;border-radius:20px;}
[data-testid="stMetric"] {background:#143223;border:1px solid #2C5A3F;border-radius:18px;padding:.8rem 1rem;}
.stTabs [data-baseweb="tab"] {font-weight:700;}
.alert {background:#143223;border-left:5px solid #E9B824;border-radius:14px;padding:1rem 1.2rem;margin:.6rem 0;line-height:1.55;}
.foot {margin:3rem 0 1rem;padding-top:1.2rem;border-top:1px solid #2C5A3F;color:#B9B39C;font-size:.9rem;text-align:center;}
.foot b {color:#E9B824;font-family:'Fraunces',serif;font-size:1.05rem;}
</style>
<div class="hero">
  <div class="org">MC2 · Société Africaine de Participation</div>
  <h1>Financer, c'est le début. Réussir, c'est être accompagné.</h1>
  <p>Un conseiller qui parle la langue du client, l'écoute au téléphone et le suit sur son champ, son étal ou sa boutique, là où l'agent de crédit ne peut pas être tous les jours.</p>
  <div class="trio"><span>Alerte météo et cultures</span><span>Caisse de poche à la voix</span><span>Bon prix, bon marché</span></div>
</div>""", unsafe_allow_html=True)

LANGS = {"Français": ("français", "fr"), "English": ("English", "en"),
         "Fufuldé (bêta)": ("fufuldé simple", "fr"), "Ewondo (bêta)": ("ewondo simple", "fr"), "Ghomala (bêta)": ("ghomala simple", "fr")}
c1, c2 = st.columns([3, 2])
farmer = c1.selectbox("Client MC2", list(D.FARMERS), key="farmer")
lname = c2.selectbox("Langue", list(LANGS), key="lang")
LANG, CODE = LANGS[lname]
if lname.endswith("(bêta)"):
    st.caption("Langue locale en bêta : le modèle essaie, la voix reste en français. Une voix native est prévue avec des partenaires de données linguistiques africains.")

if "ledger" not in st.session_state:
    st.session_state.ledger = pd.DataFrame([("vente", "5 sacs de maïs", 120000), ("dépense", "engrais NPK", 35000), ("dépense", "transport", 8000)],
                                           columns=["Type", "Objet", "Montant"])
st.session_state.setdefault("chat", [])

def speak(text):
    try:
        b = io.BytesIO(); gTTS(text, lang="en" if CODE == "en" else "fr").write_to_fp(b); return b.getvalue()
    except Exception:
        return None

def fcfa(n): return f"{n:,}".replace(",", " ") + " F"

def add_tx(text):
    tx = A.parse_transaction(text, LANG)
    st.session_state.ledger.loc[len(st.session_state.ledger)] = [tx["type"], tx["objet"], tx["montant"]]
    v, d, s = A.finance_summary(st.session_state.ledger)
    return f"Noté : {tx['type']} de {fcfa(tx['montant'])} ({tx['objet']}). Ton solde est de {fcfa(s)}."

def answer(q):
    kind = A.route(q)
    if kind == "finance": return "Caisse de poche", add_tx(q)
    if kind == "market": return "Prix du marché", A.market_agent(farmer, LANG)[0]
    return "Alerte agro-climatique", A.climate_agent(farmer, LANG)[0]

t_voice, t_clim, t_cash, t_mkt = st.tabs([":material/mic: Parler", ":material/cloud: Météo", ":material/payments: Caisse", ":material/storefront: Marché"])

with t_voice:
    @st.fragment
    def voice():
        st.markdown("Appuie sur le micro et parle. Exemple : *« J'ai vendu 3 sacs de maïs à 25 000 francs »*.")
        audio = st.audio_input("Message vocal", label_visibility="collapsed")
        typed = st.text_input("Ou écris ta question", placeholder="Quand dois-je arroser mes tomates ?")
        q = None
        if audio and audio.file_id != st.session_state.get("last_audio"):
            st.session_state.last_audio = audio.file_id
            with st.spinner("J'écoute…"):
                q = A.transcribe(audio.getvalue(), CODE)
            if not q: st.warning("Voix non reconnue. Vérifie la clé GROQ_API_KEY ou écris ta question.")
        elif typed and typed != st.session_state.get("last_typed"):
            st.session_state.last_typed = typed; q = typed
        if q:
            with st.spinner("Je réfléchis…"):
                who, r = answer(q)
            st.session_state.chat.append((q, who, r, speak(r)))
        for i, (q, who, r, wav) in enumerate(reversed(st.session_state.chat[-4:])):
            with st.chat_message("user"): st.write(q)
            with st.chat_message("assistant", avatar=":material/agriculture:"):
                st.caption(who); st.write(r)
                if wav: st.audio(wav, format="audio/mp3", autoplay=(i == 0 and bool(q)))
    voice()

with t_clim:
    @st.fragment
    def climate():
        if st.button("Générer l'alerte du jour", key="b_clim"):
            with st.spinner("Lecture des prévisions Open-Meteo…"):
                txt, df, flags = A.climate_agent(farmer, LANG)
            st.markdown(f'<div class="alert">{txt}</div>', unsafe_allow_html=True)
            st.dataframe(df, hide_index=True, use_container_width=True)
            wav = speak(txt)
            if wav: st.audio(wav, format="audio/mp3")
    climate()

with t_cash:
    @st.fragment
    def cash():
        v, d, s = A.finance_summary(st.session_state.ledger)
        a, b, c = st.columns(3); a.metric("Ventes", fcfa(v)); b.metric("Dépenses", fcfa(d)); c.metric("Solde", fcfa(s))
        with st.form("dictee", clear_on_submit=True):
            t = st.text_input("Dicte ou écris une opération", placeholder="J'ai vendu 3 sacs de maïs à 25 000 francs")
            if st.form_submit_button("Enregistrer") and t: st.success(add_tx(t)); st.rerun(scope="fragment")
        st.dataframe(st.session_state.ledger.iloc[::-1], hide_index=True, use_container_width=True)
    cash()

with t_mkt:
    @st.fragment
    def market():
        if st.button("Où et quand vendre ?", key="b_mkt"):
            with st.spinner("Comparaison des marchés…"):
                txt, df, hist = A.market_agent(farmer, LANG)
            st.markdown(f'<div class="alert">{txt}</div>', unsafe_allow_html=True)
            st.dataframe(df, hide_index=True, use_container_width=True)
            st.line_chart(hist, height=260)
            wav = speak(txt)
            if wav: st.audio(wav, format="audio/mp3")
    market()

st.markdown('<div class="foot">Projet présenté pour l\'entretien SAPA · Données de démonstration<br>Conçu et développé par <b>Romuald MBANA MEDJO</b></div>', unsafe_allow_html=True)
