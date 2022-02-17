# Mise en place de l'envionnement dev

## Prerequisites

On utilise:

- Python 3.9.7
- pip 21.2.4
- [pre-commit](https://pre-commit.com/)
- [PostgreSQL 14.0](https://www.postgresql.org/)
- [Keycloak](https://www.keycloak.org/) pour auth

## Installer

Créer l'envionnement virtuel pour python : `python -m venv ./venv`

Activer l'environnement (si nécéssaire) : `source ./venv/bin/activate`. Quand l'env est actif, on vois `(venv)` avant les commandes dans le terminal.

Installer les requirements du projet : `pip install -r requirements.txt`

Créer le BDD : `createdb bilans-climat`

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

En plus des variables d'environnement au-dessus, on a besoin de :

1. Un add-on scalingo pour OpenVPN ou, en locale, let client (OpenVPN)[https://openvpn.net/download-open-vpn/]
1. Fichier configuration d'OpenVPN (`.ovpn`) - téléchargable dès le portail keycloak
1. `ca.pem`, `cert.pem`, `key.pem` (c'est possible que ils sont dans le fichier `.ovpn`, dans ce cas là il faut qu'on les separe en trois fichiers individus et remplace les lignes dans la configuration avec `ca ca.pem`, `cert cert.pem`, `key key.pem`)
1. nom d'utilisateur et mot de passe pour le VPN

Équipe datagir : pour plus de documentation et acceder les secrets, consulter le cloud datagir.

### Staging

Pour un environnement de staging/preproduction on utilise l'environnement Keycloak preprod parce que l'environnement d'integration a besoin d'ajouter des DNS lookups soi-même, qui n'est pas possible sur les hébérgeurs.

## Tests

`python manage.py test`

## Lancer en locale

`python manage.py runserver`

Et aller à un endpoint dans votre navigateur, par exemple `localhost:8000/api/v1/bilans/`

## Contribuer

Avant committer, `pre-commit install`
