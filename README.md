# KanMind Backend

Backend-API für das KanMind Kanban-Board Projekt, entwickelt mit Django und Django REST Framework.

## 🚀 Schnellstart

### 1. Virtual Environment erstellen

```bash
cd KanMind_Backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 3. Umgebungsvariablen konfigurieren

```bash
# .env Datei ist bereits vorhanden, ggf. anpassen
```

### 4. Datenbank migrieren

```bash
python manage.py migrate
```

### 5. Superuser erstellen

```bash
python manage.py createsuperuser
```

### 6. Server starten

```bash
python manage.py runserver
```

Der Server läuft unter `http://127.0.0.1:8000/`

---

## 📁 Projektstruktur

```
KanMind_Backend/
├── core/                    # Projekt-Konfiguration
│   ├── __init__.py
│   ├── settings.py          # Hauptkonfiguration
│   ├── urls.py              # Root URL-Konfiguration
│   ├── wsgi.py
│   └── asgi.py
│
├── auth_app/                # Authentifizierung App
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py            # UserProfile Model
│   ├── admin.py
│   └── api/
│       ├── __init__.py
│       ├── serializers.py   # User, Registration Serializers
│       ├── views.py         # Registration, CurrentUser Views
│       ├── urls.py          # Auth API Routes
│       └── permissions.py   # IsOwnerOrReadOnly
│
├── kanban_app/              # Kanban Board App
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py            # Board, Column, Task, Subtask, Comment
│   ├── admin.py
│   └── api/
│       ├── __init__.py
│       ├── serializers.py   # Board, Column, Task Serializers
│       ├── views.py         # ViewSets für CRUD
│       ├── urls.py          # Kanban API Routes
│       └── permissions.py   # Board/Task Permissions
│
├── manage.py
├── requirements.txt
├── .env                     # Umgebungsvariablen (nicht committen!)
├── .env.example             # Vorlage für .env
├── .gitignore
└── README.md
```

---

## 📊 Datenmodelle

### auth_app

| Model | Beschreibung |
|-------|--------------|
| `UserProfile` | Erweitertes Benutzerprofil (Avatar-Farbe) |

### kanban_app

| Model | Beschreibung |
|-------|--------------|
| `Board` | Kanban-Board mit Titel, Beschreibung, Eigentümer, Mitglieder |
| `Column` | Spalten (To Do, In Progress, Done) mit Position |
| `Task` | Aufgaben mit Priorität, Deadline, Zuweisungen |
| `Subtask` | Unteraufgaben mit Erledigt-Status |
| `Comment` | Kommentare zu Aufgaben |

---

## 🔗 API Endpoints

### Authentifizierung (`/api/auth/`)

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| POST | `/api/auth/register/` | Neuen Benutzer registrieren |
| POST | `/api/auth/login/` | JWT Token erhalten |
| POST | `/api/auth/token/refresh/` | Token erneuern |
| GET | `/api/auth/me/` | Aktueller Benutzer |
| GET/PUT | `/api/auth/profile/` | Benutzerprofil |

### Boards (`/api/boards/`)

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/api/boards/` | Alle Boards auflisten |
| POST | `/api/boards/` | Neues Board erstellen |
| GET | `/api/boards/{id}/` | Board Details mit Spalten |
| PUT | `/api/boards/{id}/` | Board aktualisieren |
| DELETE | `/api/boards/{id}/` | Board löschen |

### Spalten (`/api/boards/{board_id}/columns/`)

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/api/boards/{id}/columns/` | Spalten eines Boards |
| POST | `/api/boards/{id}/columns/` | Neue Spalte erstellen |
| PUT | `/api/boards/{id}/columns/{col_id}/` | Spalte aktualisieren |
| DELETE | `/api/boards/{id}/columns/{col_id}/` | Spalte löschen |

### Tasks (`/api/tasks/`)

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/api/tasks/` | Alle Tasks auflisten |
| POST | `/api/tasks/` | Neue Task erstellen |
| GET | `/api/tasks/{id}/` | Task Details |
| PUT | `/api/tasks/{id}/` | Task aktualisieren |
| DELETE | `/api/tasks/{id}/` | Task löschen |
| PATCH | `/api/tasks/{id}/move/` | Task verschieben |

### Subtasks (`/api/tasks/{task_id}/subtasks/`)

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/api/tasks/{id}/subtasks/` | Subtasks einer Task |
| POST | `/api/tasks/{id}/subtasks/` | Neue Subtask |
| PATCH | `/api/tasks/{id}/subtasks/{sub_id}/toggle/` | Status wechseln |

### Kommentare (`/api/tasks/{task_id}/comments/`)

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/api/tasks/{id}/comments/` | Kommentare einer Task |
| POST | `/api/tasks/{id}/comments/` | Neuer Kommentar |
| DELETE | `/api/tasks/{id}/comments/{com_id}/` | Kommentar löschen |

---

## 🔒 Authentifizierung

Das Projekt verwendet **JWT (JSON Web Tokens)**.

### Token erhalten

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'
```

### API-Anfrage mit Token

```bash
curl http://127.0.0.1:8000/api/boards/ \
  -H "Authorization: Bearer <access_token>"
```

---

## ⚙️ Konfiguration

### Umgebungsvariablen (.env)

```env
SECRET_KEY=dein-geheimer-schluessel
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=7
```

---

## 🛠️ Entwicklung

### Migrations erstellen

```bash
python manage.py makemigrations
python manage.py migrate
```

### Admin-Oberfläche

Verfügbar unter `http://127.0.0.1:8000/admin/`

---

## 📝 Lizenz

Dieses Projekt ist ausschließlich für Schüler der Developer Akademie bestimmt.
