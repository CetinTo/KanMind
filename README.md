# KanMind Backend

Backend API for the KanMind Kanban Board project, built with Django and Django REST Framework.

## 🚀 Quick Start

### 1. Create Virtual Environment

```bash
cd KanMind_Backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

###3. Configure Environment Variables

```bash
# .env file already exists, adjust if needed
```

###  4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Start Server

```bash
python manage.py runserver
```

Server runs at `http://127.0.0.1:8000/`

---

## 📁 Project Structure

```
KanMind_Backend/
├── core/                    # Project configuration
│   ├── __init__.py
│   ├── settings.py          # Main configuration
│   ├── urls.py              # Root URL configuration
│   ├── wsgi.py
│   └── asgi.py
│
├── auth_app/                # Authentication app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py            # UserProfile model
│   ├── admin.py
│   └── api/
│       ├── __init__.py
│       ├── serializers.py   # User, Registration serializers
│       ├── views.py         # Registration, CurrentUser views
│       ├── urls.py          # Auth API routes
│       └── permissions.py   # IsOwnerOrReadOnly
│
├── kanban_app/              # Kanban board app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py            # Board, Column, Task, Subtask, Comment
│   ├── admin.py
│   └── api/
│       ├── __init__.py
│       ├── serializers.py   # Board, Column, Task serializers
│       ├── views.py         # CRUD ViewSets
│       ├── urls.py          # Kanban API routes
│       └── permissions.py   # Board/Task permissions
│
├── manage.py
├── requirements.txt
├── .env                     # Environment variables (do NOT commit)
├── .env.example             # Example .env file
├── .gitignore
└── README.md
```

---

## 📊 Data Models

### auth_app

| Model | Description|
|-------|--------------|
| `UserProfile` | Extended user profile (avatar color)|

### kanban_app

| Model | Description |
|-------|--------------|
| `Board`   | Kanban board with title, description, owner and members |
| `Column`  |Board columns (To Do, In Progress, Done) |
| `Task`    | Tasks with priority, deadline and assignments |
| `Subtask` | Subtasks with completion status |
| `Comment` | Task comments |

---

## 🔗 API Endpoints

### Authentication (`/api/auth/`)

|Method | Endpoint | Description|
|---------|----------|--------------|
| POST | `/api/auth/registration/` | Registration new user |
| POST | `/api/auth/login/` | Get JWT token |
| POST | `/api/auth/token/refresh/` | Refresh token |
| GET | `/api/auth/me/` | Current user |
| GET/PUT | `/api/auth/profile/` | User profile |

### Boards (`/api/boards/`)

| Method | Endpoint | Description |
|---------|----------|--------------|
| GET | `/api/boards/` | List all boards |
| POST | `/api/boards/` | Create board |
| GET | `/api/boards/{id}/` | Board details |
| PUT | `/api/boards/{id}/` | Update board|
| DELETE | `/api/boards/{id}/` | Delete board |

### Columns (`/api/boards/{board_id}/columns/`)

| Method | Endpoint | Description  |
|---------|----------|--------------|
| GET | `/api/boards/{id}/columns/` | List columns |
| POST | `/api/boards/{id}/columns/` |Create column |
| PUT | `/api/boards/{id}/columns/{col_id}/` | Update column |
| DELETE | `/api/boards/{id}/columns/{col_id}/` | Delete column |

### Tasks (`/api/tasks/`)

| Method | Endpoint | Description  |
|---------|----------|--------------|
| GET | `/api/tasks/` | List tasks |
| POST | `/api/tasks/` |Create task|
| GET | `/api/tasks/{id}/` | Task details |
| PUT | `/api/tasks/{id}/` | Update task |
| DELETE | `/api/tasks/{id}/` |Delete task |
| PATCH | `/api/tasks/{id}/move/` | Move task|

### Subtasks (`/api/tasks/{task_id}/subtasks/`)

| Methode | Endpoint | Description  |
|---------|----------|--------------|
| GET | `/api/tasks/{id}/subtasks/` | List subtasks |
| POST | `/api/tasks/{id}/subtasks/` |Create subtask |
| PATCH | `/api/tasks/{id}/subtasks/{sub_id}/toggle/` | Toggle subtask status|

### Comments (`/api/tasks/{task_id}/comments/`)

| Methode | Endpoint | Description  |
|---------|----------|--------------|
| GET | `/api/tasks/{id}/comments/` |List comments |
| POST | `/api/tasks/{id}/comments/` | Create comment |
| DELETE | `/api/tasks/{id}/comments/{com_id}/` | Delete comment |

---

## 🔒 Authentication

This project uses **JWT (JSON Web Tokens)**.

### Get token

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'
```

### Use token

```bash
curl http://127.0.0.1:8000/api/boards/ \
  -H "Authorization: Bearer <access_token>"
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
SECRET_KEY=dein-geheimer-schluessel
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
ACCESS_TOKEN_LIFETIME_MINUTES=60
REFRESH_TOKEN_LIFETIME_DAYS=7
```

---

## 🛠️ Development

### Create Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Admin Panel

Available at `http://127.0.0.1:8000/admin/`

---

## 📝 Lizenz

This project is intended exclusively for students of the Developer Akademie.