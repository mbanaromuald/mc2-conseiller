"""Trois agents spécialisés + un routeur. LLM et Whisper via Groq ; météo via Open-Meteo (sans clé).
Sans clé GROQ_API_KEY, chaque agent retombe sur une réponse déterministe : la démo ne plante jamais."""
import os, re, json, requests, pandas as pd
from groq import Groq
import data as D

MODEL = "llama-3.3-70b-versatile"
PERSONA = ("Tu es le Conseiller MC2, un conseiller agricole et financier de confiance pour les clients d'une "
           "mutuelle communautaire de croissance (MC2) au Cameroun. Phrases très courtes, mots simples, ton chaleureux, "
           "60 mots maximum, un seul conseil concret. Réponds en {lang}.")

def _client():
    k = os.getenv("GROQ_API_KEY")
    return Groq(api_key=k) if k else None

def llm(user, lang, fallback, system=None, as_json=False):
    c = _client()
    if not c: return fallback
    try:
        kw = {"response_format": {"type": "json_object"}} if as_json else {}
        r = c.chat.completions.create(model=MODEL, temperature=0.3, **kw, messages=[
            {"role": "system", "content": (system or PERSONA).format(lang=lang)}, {"role": "user", "content": user}])
        return r.choices[0].message.content.strip()
    except Exception:
        return fallback

def transcribe(audio: bytes, code="fr") -> str:
    c = _client()
    if not c: return ""
    try:
        return c.audio.transcriptions.create(file=("voix.wav", audio), model="whisper-large-v3", language=code).text
    except Exception:
        return ""

# ---------- Agent 1 : alerte agro-climatique ----------
def weather(lat, lon) -> pd.DataFrame:
    try:
        d = requests.get("https://api.open-meteo.com/v1/forecast", timeout=8, params=dict(
            latitude=lat, longitude=lon, timezone="auto", forecast_days=5,
            daily="temperature_2m_max,precipitation_probability_max,precipitation_sum")).json()["daily"]
        return pd.DataFrame({"Jour": d["time"], "Temp max (°C)": d["temperature_2m_max"],
                             "Pluie (%)": d["precipitation_probability_max"], "Pluie (mm)": d["precipitation_sum"]})
    except Exception:  # hors-ligne : données de secours
        return pd.DataFrame({"Jour": pd.date_range("today", periods=5).strftime("%Y-%m-%d"), "Temp max (°C)": [31, 33, 34, 30, 29],
                             "Pluie (%)": [10, 20, 15, 80, 85], "Pluie (mm)": [0, 0, 0, 12, 18]})

def climate_flags(crop, df):
    f, dry = [], int((df["Pluie (%)"] < 30).sum())
    if dry >= 3 or df["Temp max (°C)"].max() > 33: f.append("Chaleur ou sécheresse : irriguer tôt le matin ou le soir.")
    if crop == "Tomate" and (df["Pluie (%)"] > 70).any(): f.append("Pluies fortes prévues : risque de mildiou, traiter avant la pluie.")
    if crop == "Maïs" and (df["Pluie (mm)"] > 10).any(): f.append("Grosse pluie attendue : ne pas épandre l'engrais avant.")
    if crop == "Manioc" and (df["Pluie (mm)"] > 15).any(): f.append("Sols détrempés : surveiller la pourriture des racines.")
    return f or ["Temps favorable : poursuivre les travaux normalement."]

def climate_agent(name, lang):
    p = D.FARMERS[name]; df = weather(p["lat"], p["lon"]); flags = climate_flags(p["crop"], df)
    txt = llm(f"Culture : {p['crop']} à {p['zone']}. Prévisions 5 jours : {df.to_dict('records')}. Risques : {flags}. "
              "Rédige l'alerte vocale pour l'agriculteur.", lang, " ".join(flags))
    return txt, df, flags

# ---------- Agent 2 : gestion financière de poche ----------
def parse_transaction(text, lang="français"):
    fb_kind = "vente" if re.search(r"vend|vente|sold|sell", text, re.I) else "dépense"
    nums = [int(n.replace(" ", "")) for n in re.findall(r"\d[\d ]*", text)]
    fb = dict(type=fb_kind, objet=text[:40], montant=max(nums) if nums else 0)
    out = llm(f"Texte dicté : « {text} ». Extrais en JSON : type (vente ou dépense), objet (court), montant (total en FCFA, nombre entier).",
              lang, json.dumps(fb), system="Tu extrais des transactions financières. Réponds uniquement en JSON valide.", as_json=True)
    try:
        j = json.loads(out); return dict(type=j["type"], objet=j["objet"], montant=int(j["montant"]))
    except Exception:
        return fb

def finance_summary(ledger: pd.DataFrame):
    v = ledger.loc[ledger["Type"] == "vente", "Montant"].sum(); d = ledger.loc[ledger["Type"] == "dépense", "Montant"].sum()
    return int(v), int(d), int(v - d)

# ---------- Agent 3 : prix du marché ----------
def market_analysis(name):
    p = D.FARMERS[name]; crop, zone = p["crop"], p["zone"]; rows = []
    for m, hist in D.PRICES[crop].items():
        t = D.TRANSPORT[zone].get(m)
        if t is None: continue
        rows.append(dict(Marché=m, Prix=hist[-1], Transport=t, Net=hist[-1] - t, Tendance=hist[-1] - hist[-4]))
    df = pd.DataFrame(rows).sort_values("Net", ascending=False).reset_index(drop=True)
    return df, pd.DataFrame(D.PRICES[crop], index=D.WEEKS)

def market_agent(name, lang):
    df, hist = market_analysis(name); best = df.iloc[0]; crop = D.FARMERS[name]["crop"]
    action = "vendre maintenant" if best["Tendance"] <= 0 else "attendre 1 à 2 semaines, les prix montent"
    fb = f"Meilleur marché : {best['Marché']}, {best['Net']:,} F net par sac après transport. Conseil : {action}.".replace(",", " ")
    return llm(f"Culture : {crop}. Classement net des marchés : {df.to_dict('records')}. Conseil calculé : {action}. "
               "Explique où et quand vendre.", lang, fb), df, hist

# ---------- Routeur ----------
def route(text):
    fb = ("finance" if re.search(r"vend|achet|pay|dépens|franc|fcfa|sac", text, re.I) else
          "market" if re.search(r"prix|march|vendre où|quand vendre", text, re.I) else "climate")
    r = llm(f"Question : « {text} ». Classe en climate (météo, irrigation, maladies), finance (ventes, dépenses, caisse) ou "
            "market (prix, où/quand vendre). Réponds par un seul mot.", "français", fb,
            system="Tu es un routeur d'intentions. Réponds par un seul mot.").lower()
    return next((k for k in ("climate", "finance", "market") if k in r), fb)
