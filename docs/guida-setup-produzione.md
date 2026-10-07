# Guida setup produzione — Juventum

Data: 2026-09-10
Scopo: checklist passo-passo per portare Juventum online (Sviluppo #1
della roadmap interna). Nessun
passaggio richiede scrivere codice — solo account e configurazione.
Il workflow GitHub Actions per il refresh dati va scritto dopo, in
sessione separata (è codice, non setup account).

## Ordine dei passi

1. Neon (DB Postgres di produzione)
2. Render (hosting backend FastAPI)
3. Vercel (frontend — account già esistente, solo configurazione)
4. cron-job.org (ping periodico per live poll e warm-up)

## 1. Neon — database Postgres

1. Vai su neon.tech, registrati (login con GitHub va bene).
2. Crea un progetto, nome `juventum`, regione EU (Frankfurt — più
   vicina).
3. Neon crea un DB di default (`neondb`) — va bene così, o rinominalo.
4. Dalla dashboard del progetto → "Connection string" → copia la
   stringa col driver diretto `postgresql://` (non quella pooled per
   ora).
5. **Non incollare la stringa in chat con Claude.** Mettila tu
   direttamente in `backend/.env` locale come nuova variabile, es.
   `PROD_DATABASE_URL=...`. Il file `.env` è già gitignored.

## 2. Render — hosting backend

1. Vai su render.com, registrati (login con GitHub).
2. "New" → "Web Service" → collega il repo `juventum` su GitHub.
3. Render rileva il `Dockerfile` in `backend/` — impostalo come root
   directory del servizio (`backend`).
4. Health check path: `/healthz`.
5. Variabili d'ambiente da impostare nel pannello Render (valori dai
   tuoi file `.env` locali, non incollarli in chat):
   - `DATABASE_URL` = la connection string Neon del passo 1
   - `FOOTBALL_DATA_API_KEY`
   - `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`, `VAPID_SUBJECT`
   - `ADMIN_TOKEN` (generane uno nuovo, es. `openssl rand -hex 32`)
   - `CORS_ORIGINS` (aggiungi l'URL Vercel una volta noto, passo 3)
6. Deploy. Alla fine avrai un URL tipo `https://juventum-xxxx.onrender.com`.
7. Verifica: `curl https://<url-render>/healthz` deve rispondere 200.

## 3. Vercel — frontend (account già esistente)

1. Import del repo `juventum` su Vercel, root directory `frontend`.
2. Variabili d'ambiente:
   - `NEXT_PUBLIC_API_BASE_URL` = URL Render del passo 2
   - `NEXT_PUBLIC_VAPID_PUBLIC_KEY` = stessa chiave pubblica VAPID di
     Render
3. Deploy. Copia l'URL Vercel definitivo.
4. Torna su Render, aggiorna `CORS_ORIGINS` con l'URL Vercel, redeploy.

## 4. cron-job.org — ping periodico

1. Registrati su cron-job.org (gratuito).
2. Job 1 — warm-up: `GET https://<url-render>/healthz` ogni 10 minuti,
   sempre attivo. Tiene sveglio Render free tier.
3. Job 2 — live poll: `POST https://<url-render>/admin/poll-live` con
   header `X-Admin-Token: <valore ADMIN_TOKEN>`, ogni 2-3 minuti. Puoi
   attivarlo solo nei giorni di partita, o lasciarlo sempre acceso
   (costa solo una query a vuoto quando non c'è partita).

## Dopo questi 4 passi

Quando tutto sopra è fatto e verificato (healthz risponde, frontend
Vercel raggiunge il backend Render, DB Neon collegato), si torna alla
sessione di brainstorming per:

- prima ingestione reale su Neon (`python -m app.ingestion.ingest` con
  `DATABASE_URL` = Neon, poi `scripts/check_team_names.py`)
- workflow GitHub Actions per il refresh dati giornaliero (cron
  `0 2 * * *`, secrets `DATABASE_URL` e `FOOTBALL_DATA_API_KEY`)
- decisione su come dismettere/tenere il cron locale (`launchd`)
- tabella `ingest_runs` e `last_successful_ingest_at` su `/healthz`
  per la freschezza dati visibile in UI

