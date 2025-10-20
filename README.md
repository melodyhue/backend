# MelodyHue – Backend (FastAPI)

[![GitHub Release](https://img.shields.io/github/v/release/melodyhue/backend)](https://github.com/melodyhue/backend/releases)
[![GitHub Release Date](https://img.shields.io/github/release-date/melodyhue/backend)](https://github.com/melodyhue/backend/releases)
[![GitHub License](https://img.shields.io/github/license/melodyhue/backend)](https://github.com/melodyhue/backend/blob/main/LICENSE)
[![GitHub contributors](https://img.shields.io/github/contributors/melodyhue/backend)](https://github.com/melodyhue/backend/graphs/contributors)
[![GitHub Packages](https://img.shields.io/badge/GitHub%20Packages-ghcr.io-blue)](https://github.com/melodyhue/backend/pkgs/container/backend)
[![GitHub Issues](https://img.shields.io/github/issues/melodyhue/backend)](https://github.com/melodyhue/backend/issues)
[![CI/CD - Docker](https://github.com/melodyhue/backend/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/melodyhue/backend/actions/workflows/ci-cd.yml)

API FastAPI multi‑utilisateurs qui expose la musique Spotify en cours et calcule une couleur dominante depuis la pochette. Auth JWT (access/refresh), gestion des overlays (nom + template), couleur d’overlay héritée des paramètres utilisateur, et endpoints publics pour l’affichage.

—

## ✨ Points clés

- FastAPI + SQLAlchemy
- Auth JWT (HS256): access 15 min, refresh 30 jours (configurable)
- Overlays: name + template; la couleur provient de `UserSetting.default_overlay_color`
- Endpoints `/color` et `/infos` par utilisateur, avec fallback couleur en pause
- Reset mot de passe par e‑mail (SMTP)
- Déploiement Docker / Docker Compose

—

## 🚀 Démarrage rapide

### A. Local (dev)

1) Installer
```powershell
pip install -r requirements.txt
```
2) Variables d’environnement (voir plus bas). Exemple minimal: DB_*, SECRET_KEY, ENCRYPTION_KEY.
3) Lancer en dev (reload)
```powershell
python -m uvicorn app.asgi:app --host 0.0.0.0 --port 8765 --reload
```
4) Health
- http://localhost:8765/health

### B. Docker Compose

`docker-compose.yml` fournit un service `backend` (port hôte 8494 par défaut). Adaptez vos variables .env puis lancez:
```powershell
docker compose up -d
```

—

## 🔧 Variables d’environnement (extrait)

- App
  - `SECRET_KEY`, `ENABLE_CORS`, `CORS_ALLOW_ORIGINS`, `CORS_ALLOW_CREDENTIALS`
- DB
  - `DB_HOST`, `DB_DATABASE`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`
- Auth
  - `ACCESS_TOKEN_EXPIRE_MIN` (def 15), `REFRESH_TOKEN_EXPIRE_DAYS` (def 30), `JWT_SECRET`, `JWT_ALG`
- SMTP (reset mdp)
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_STARTTLS=true/false`, `SMTP_SSL=true/false`, `SMTP_FROM`, `SMTP_FROM_NAME`
  - `FRONTEND_URL` ou `PASSWORD_RESET_URL_BASE` (ex: `https://app/auth/reset?token=`)

Générer des clés
```powershell
# SECRET_KEY (32 bytes hex)
python -c "import secrets; print(secrets.token_hex(32))"
# ENCRYPTION_KEY (Fernet)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

—

## 🧭 Endpoints (aperçu)

- Auth
  - POST `/auth/register` → 200: tokens; 409 si email déjà pris
  - POST `/auth/login` → 200: tokens ou 200 `requires_2fa`; 401 si identifiants invalides
  - POST `/auth/login/2fa` → tokens (si 2FA)
  - POST `/auth/refresh` → rotation refresh + nouveau couple tokens
  - POST `/auth/forgot` → envoie un mail avec lien de reset
  - POST `/auth/reset` → change le mot de passe (token valide 1h)

- Overlays (privé)
  - GET `/overlays/` – liste de vos overlays
  - POST `/overlays/` – crée un overlay `{ name, template }`
  - GET `/overlays/{id}` – détail (propriétaire uniquement)
  - PATCH `/overlays/{id}` – met à jour `{ name?, template? }`
  - POST `/overlays/{id}/duplicate` – duplique
  - DELETE `/overlays/{id}` – supprime

- Overlays (public)
  - GET `/overlay/{id}` – lecture publique d’un overlay (sans auth)

- Couleurs / Infos (public par utilisateur)
  - GET `/infos/{user_id}` – couleur + infos piste; en pause, couleur = `default_overlay_color`
  - GET `/color/{user_id}` – couleur seule; en pause, couleur = `default_overlay_color`

- Paramètres utilisateur (privé)
  - GET `/settings/me` – récupère vos préférences (incl. `default_overlay_color`)
  - PATCH `/settings/me` – met à jour (incl. `default_overlay_color`)

—

## 🔐 Auth & sécurité (résumé)

- Access token: 15 min (config `ACCESS_TOKEN_EXPIRE_MIN`)
- Refresh token: 30 jours (config `REFRESH_TOKEN_EXPIRE_DAYS`), rotation à chaque refresh
- Login: username OU email + password (usernames non uniques; email unique)
- 2FA TOTP (optionnel) avec secret otpauth://

—

## 🎨 Overlays & couleur

- Un overlay = `{ id, name, template, created_at, updated_at }`
- La couleur ne se règle pas sur l’overlay. Elle provient de `UserSetting.default_overlay_color` et s’applique:
  - dans `/color` et `/infos` quand la musique est en pause ou indisponible
  - immédiatement après mise à jour via `PATCH /settings/me`

—

## 📮 Reset mot de passe (e‑mail)

1) POST `/auth/forgot` avec email → crée un token (validité 1h) et envoie un lien
2) Le lien pointe vers votre front (config `PASSWORD_RESET_URL_BASE`, ex: `https://app/auth/reset?token=`)
3) POST `/auth/reset` avec `{ token, new_password }`

Astuce: en dev, `EMAIL_DEBUG=true` renvoie aussi le token brut dans la réponse.

—

## 🛠️ Dev

- Lancer en dev: uvicorn avec `--reload`
- Vérifier la DB: la création des tables et quelques migrations légères sont gérées au démarrage
- Ports: dev 8765 (uvicorn), Docker 8494 (exposé par compose)

—

## 🔗 Liens

- Frontend: https://github.com/melodyhue/frontend

—

## 🤝 Contribuer

- Issues et PR bienvenues. Merci de décrire clairement le contexte, les endpoints et la reproduction.

## 📄 Licence

MIT – voir [LICENSE](LICENSE).
