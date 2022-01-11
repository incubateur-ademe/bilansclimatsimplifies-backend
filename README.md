# Mise en place de l'envionnement dev

## Prerequisites

On utilise:

- Python 3.9.7
- pip 21.2.4
- [pre-commit](https://pre-commit.com/)
- [PostgreSQL 14.0](https://www.postgresql.org/)
- [Keycloak](https://www.keycloak.org/) pour auth

## Installer

Créer le BDD : `createdb bilans-climat`

Créer l'envionnement virtuel pour python : `python -m venv ./venv`

Activer l'environnement (si nécéssaire) : `source ./venv/bin/activate`. Quand l'env est actif, on vois `(venv)` avant les commandes dans le terminal.

Installer les requirements du projet : `pip install -r requirements.txt`

Lancer keycloak en local `docker run -p 8080:8080 -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=admin quay.io/keycloak/keycloak:15.0.2` et créer le realm `myrealm`, client, et utilisateur. [En lisant plus du setup](https://www.keycloak.org/getting-started/getting-started-docker).

## Variables d'environnement

```
SECRET=(vous pouvez utiliser [l'outil Djecrety](https://djecrety.ir/) pour le générer)
FORCE_HTTPS=False (True si c'est pas pour dév local)
DEBUG=True
ALLOWED_HOSTS='localhost, *'
DB_USER=
DB_NAME=
DB_PASSWORD=
DB_PORT=5432
DB_HOST=127.0.0.1
CORS_ORIGIN_WHITELIST='http://localhost:3000'
CSRF_TRUSTED_ORIGINS='http://localhost:3000'
JWT_ISSUER="http://localhost:8080/auth/realms/myrealm"
JWT_CERTS_URL="http://localhost:8080/auth/realms/myrealm/protocol/openid-connect/certs"
KOUMOUL_API_KEY=
KOUMOUL_API_URL="https://koumoul.com/data-fair/api/v1/datasets/bilans-climat-simplifies/"
AUTH_CLIENT_ID=
AUTH_CLIENT_SECRET=
AUTH_KEYCLOAK=
AUTH_REALM=
AUTH_USERS_API=
AUTH_PASS_REDIRECT_URI=
```

## VPN

Il faut qu'on connecte par VPN au ademe connect pour créer les comptes.

<!-- TODO: complete instructions -->

<!-- TODO: instructions for making someone an admin for full report export purposes -->

## Tests

`python manage.py test`

## Lancer en locale

`python manage.py runserver`

Et aller à un endpoint dans votre navigateur, par exemple `localhost:8000/api/v1/bilans/`

## Contribuer

Avant committer, `pre-commit install`
