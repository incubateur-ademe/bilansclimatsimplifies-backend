# Mise en place de l'envionnement dev

## Prerequisites

On utilise:

- Python 3.9.7
- pip 21.2.4
- [pre-commit](https://pre-commit.com/)
- [PostgreSQL 14.0](https://www.postgresql.org/)

## Installer

Créer le BDD : `createdb bilans-climat`

Créer l'envionnement virtuel pour python : `python -m venv ./venv`

Activer l'environnement (si nécéssaire) : `source ./venv/bin/activate`. Quand l'env est actif, on vois `(venv)` avant les commandes dans le terminal.

Installer les requirements du projet : `pip install -r requirements.txt`

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
```

## Tests

`python manage.py test`

## Lancer en locale

`python manage.py runserver`

Et aller à un endpoint dans votre navigateur, par exemple `localhost:8000/api/v1/bilans/`

## Contribuer

Avant committer, `pre-commit install`
