# 🎫 Ticket System

A complete IT Help Desk ticketing system with **user authentication**, role-based access control, and a modern dark UI.

## Features

### Authentication & Authorization
- ✅ **User Registration** — Anyone can sign up as a regular user
- ✅ **Login/Logout** — Secure session-based authentication with password hashing
- ✅ **Role-Based Access** — Three roles: Admin, Agent, User
- ✅ **User Management** — Admins can activate/deactivate users and change roles
- ✅ **Profile Page** — View profile info and change password

### Ticket Management
- ✅ **Create Tickets** — Logged-in users submit support requests
- ✅ **Ticket Lifecycle** — Open → In Progress → Resolved → Closed
- ✅ **Comments** — Public and internal (agent-only) notes
- ✅ **Assignment** — Assign tickets to agents/admins
- ✅ **Filtering & Search** — By status, priority, category, or keyword

### Dashboard
- ✅ **Stats Overview** — Total, Open, In Progress, Resolved, Closed, High Priority
- ✅ **Recent Tickets** — Quick view of latest tickets
- ✅ **Quick Actions** — Fast navigation to common tasks

### Security
- ✅ **Password Hashing** — Werkzeug secure password storage
- ✅ **Session Management** — Flask sessions with secret keys
- ✅ **Route Protection** — Decorators for login, agent, and admin access
- ✅ **Permission Checks** — Users only see their own tickets

## Role Permissions

| Feature | Admin | Agent | User |
|---------|-------|-------|------|
| View all tickets | ✅ | ✅ | ❌ (own only) |
| Create tickets | ✅ | ✅ | ✅ |
| Update status/priority | ✅ | ✅ | ❌ |
| Assign tickets | ✅ | ✅ | ❌ |
| Add internal comments | ✅ | ✅ | ❌ |
| Delete tickets | ✅ | ❌ | ❌ |
| Manage users | ✅ | ❌ | ❌ |
| Change roles | ✅ | ❌ | ❌ |

## Default Accounts

| Username | Password | Role | Email |
|----------|----------|------|-------|
| `admin` | `admin123` | Admin | admin@ticketsystem.com |
| `ibrahim` | `password123` | Admin | shawady6@gmail.com |
| `agent1` | `agent123` | Agent | agent@company.com |

> ⚠️ **Change these passwords in production!**

## Tech Stack

- **Backend:** Python 3, Flask, SQLAlchemy, Werkzeug
- **Database:** SQLite (auto-created)
- **Frontend:** HTML5, CSS3, Vanilla JS
- **Icons:** Font Awesome 6
- **Container:** Docker + Docker Compose

## Quick Start (Docker)

```bash
cd ticket_system
docker-compose up -d --build
```

Open: `http://localhost:5000`

## Quick Start (Local)

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python app.py

# 5. Open http://localhost:5000
```

## Docker Commands

| Command | Description |
|---------|-------------|
| `docker-compose up -d --build` | Build & start |
| `docker-compose up -d` | Start existing |
| `docker-compose down` | Stop & remove |
| `docker-compose logs -f` | View logs |
| `docker-compose restart` | Restart |

## Project Structure

```
ticket_system/
├── app.py                 # Flask app with auth & routes
├── requirements.txt       # Dependencies
├── Dockerfile             # Docker image
├── docker-compose.yml     # Docker orchestration
├── README.md
├── static/
│   ├── css/style.css     # Styles
│   └── js/main.js        # JavaScript
└── templates/
    ├── base.html         # Layout with auth nav
    ├── login.html        # Login page
    ├── register.html     # Registration page
    ├── index.html        # Dashboard
    ├── tickets.html      # Ticket list
    ├── ticket_detail.html # Single ticket
    ├── create_ticket.html # New ticket form
    ├── agents.html       # Agent list
    ├── users.html        # User management (admin)
    └── profile.html     # User profile
```

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/stats` | GET | Any | Ticket statistics |
| `/api/tickets` | GET | Any | All tickets as JSON |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `your-secret-key...` | Flask secret key |
| `FLASK_DEBUG` | `False` | Debug mode |

## Production Checklist

- [ ] Change `SECRET_KEY` to a strong random string
- [ ] Change all default passwords
- [ ] Use HTTPS (Nginx/Traefik reverse proxy)
- [ ] Backup `tickets.db` regularly
- [ ] Consider PostgreSQL instead of SQLite
- [ ] Add email notifications
- [ ] Set up log monitoring

## License

Built by Ibrahim Elsaid Elshawady
