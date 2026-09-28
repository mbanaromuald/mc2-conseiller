# Conseiller Agricole Virtuel MC2 — par Romuald MBANA MEDJO

## Lancer avec Docker
```bash
cp .env.example .env      # y mettre votre clé Groq (gratuite : console.groq.com)
docker compose up --build # puis ouvrir http://localhost:8501
```
Sans clé, l'application fonctionne en mode secours (règles déterministes, sans voix entrante).

## Architecture
- `agents.py` : agent agro-climatique (Open-Meteo), agent caisse de poche (extraction JSON d'une dictée), agent prix de marché (prix net après transport + tendance), routeur d'intention.
- Groq : Llama 3.3 70B (raisonnement) et Whisper large-v3 (transcription). gTTS : réponse vocale.
- `data.py` : portefeuille et prix simulés (à remplacer par les données réelles de la MC2).

## Limites à assumer en entretien
- Whisper et les voix TTS grand public ne couvrent pas correctement le fufuldé, l'ewondo ou le ghomala. Le prototype démontre le parcours en français/anglais ; les langues locales sont en bêta (texte). Feuille de route : jeux de données et partenaires linguistiques africains, puis canal WhatsApp Business API.
- Données de marché simulées : à connecter aux relevés terrain des agents MC2.
