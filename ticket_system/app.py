from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== DATABASE MODELS ====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, agent, team_leader, user
    team = db.Column(db.String(50), nullable=True)  # IT, Network, Support, etc.
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='General')
    priority = db.Column(db.String(20), default='Medium')
    status = db.Column(db.String(20), default='Open')
    requester_name = db.Column(db.String(100), nullable=False)
    requester_email = db.Column(db.String(120), nullable=False)
    assigned_to = db.Column(db.String(100), default='Unassigned')
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    team = db.Column(db.String(50), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    closed_by = db.Column(db.String(100), nullable=True)
    closed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    comments = db.relationship('Comment', backref='ticket', lazy=True, cascade='all, delete-orphan')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_internal = db.Column(db.Boolean, default=False)

# ==================== AUTH DECORATORS ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def agent_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or user.role not in ['admin', 'agent', 'team_leader']:
            flash('Agent/Team Leader access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def team_leader_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or user.role not in ['admin', 'team_leader']:
            flash('Team Leader access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== CONTEXT PROCESSOR ====================

@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return dict(current_user=user)

# ==================== AUTH ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Your account has been deactivated. Contact an administrator.', 'danger')
                return redirect(url_for('login'))

            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            user.last_login = datetime.utcnow()
            db.session.commit()

            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            role='user'
        )
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    user = User.query.get(session['user_id'])
    current = request.form.get('current_password')
    new = request.form.get('new_password')
    confirm = request.form.get('confirm_password')

    if not check_password_hash(user.password_hash, current):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('profile'))

    if new != confirm:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('profile'))

    user.password_hash = generate_password_hash(new)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('profile'))

# ==================== MAIN ROUTES ====================

@app.route('/')
@login_required
def index():
    user = User.query.get(session['user_id'])

    ticket_query = Ticket.query
    if user.role == 'user':
        ticket_query = ticket_query.filter_by(created_by=user.id)
    elif user.role == 'team_leader':
        ticket_query = ticket_query.filter_by(team=user.team)

    stats = {
        'total': ticket_query.count(),
        'open': ticket_query.filter_by(status='Open').count(),
        'in_progress': ticket_query.filter_by(status='In Progress').count(),
        'resolved': ticket_query.filter_by(status='Resolved').count(),
        'closed': ticket_query.filter_by(status='Closed').count(),
        'critical': ticket_query.filter_by(priority='Critical').count(),
        'high': ticket_query.filter_by(priority='High').count()
    }

    recent_tickets = ticket_query.order_by(Ticket.created_at.desc()).limit(5).all()
    agents = User.query.filter(User.role.in_(['admin', 'agent', 'team_leader']), User.is_active==True).all()

    return render_template('index.html', stats=stats, recent_tickets=recent_tickets, agents=agents)

@app.route('/tickets')
@login_required
def tickets():
    user = User.query.get(session['user_id'])
    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', 'all')
    category_filter = request.args.get('category', 'all')
    team_filter = request.args.get('team', 'all')
    search = request.args.get('search', '')

    query = Ticket.query

    if user.role == 'user':
        query = query.filter_by(created_by=user.id)
    elif user.role == 'team_leader':
        query = query.filter_by(team=user.team)

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    if priority_filter != 'all':
        query = query.filter_by(priority=priority_filter)
    if category_filter != 'all':
        query = query.filter_by(category=category_filter)
    if team_filter != 'all':
        query = query.filter_by(team=team_filter)
    if search:
        query = query.filter(
            db.or_(
                Ticket.title.contains(search),
                Ticket.description.contains(search),
                Ticket.requester_name.contains(search)
            )
        )

    tickets = query.order_by(Ticket.created_at.desc()).all()
    agents = User.query.filter(User.role.in_(['admin', 'agent', 'team_leader']), User.is_active==True).all()

    return render_template('tickets.html', tickets=tickets, agents=agents,
                         status_filter=status_filter, priority_filter=priority_filter,
                         category_filter=category_filter, team_filter=team_filter, search=search)

@app.route('/ticket/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    user = User.query.get(session['user_id'])
    ticket = Ticket.query.get_or_404(ticket_id)

    if user.role == 'user' and ticket.created_by != user.id:
        flash('You do not have permission to view this ticket.', 'danger')
        return redirect(url_for('tickets'))

    if user.role == 'team_leader' and ticket.team != user.team:
        flash('You do not have permission to view this ticket.', 'danger')
        return redirect(url_for('tickets'))

    agents = User.query.filter(User.role.in_(['admin', 'agent', 'team_leader']), User.is_active==True).all()
    return render_template('ticket_detail.html', ticket=ticket, agents=agents)

@app.route('/create_ticket', methods=['GET', 'POST'])
@login_required
def create_ticket():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        ticket = Ticket(
            title=request.form['title'],
            description=request.form['description'],
            category=request.form['category'],
            priority=request.form['priority'],
            requester_name=user.full_name,
            requester_email=user.email,
            created_by=user.id,
            team=request.form.get('team', user.team)
        )
        db.session.add(ticket)
        db.session.commit()
        flash('Ticket created successfully!', 'success')
        return redirect(url_for('ticket_detail', ticket_id=ticket.id))

    return render_template('create_ticket.html')

@app.route('/update_ticket/<int:ticket_id>', methods=['POST'])
@agent_required
def update_ticket(ticket_id):
    user = User.query.get(session['user_id'])
    ticket = Ticket.query.get_or_404(ticket_id)
    old_status = ticket.status
    ticket.status = request.form.get('status', ticket.status)
    ticket.priority = request.form.get('priority', ticket.priority)
    ticket.assigned_to = request.form.get('assigned_to', ticket.assigned_to)
    ticket.team = request.form.get('team', ticket.team)
    ticket.category = request.form.get('category', ticket.category)

    assigned_to_id = request.form.get('assigned_to_id')
    if assigned_to_id:
        ticket.assigned_to_id = assigned_to_id

    # Track who closed the ticket and when
    if old_status != 'Closed' and ticket.status == 'Closed':
        ticket.closed_by = user.full_name
        ticket.closed_by_id = user.id
        ticket.closed_at = datetime.utcnow()

    if ticket.status == 'Resolved' and not ticket.resolved_at:
        ticket.resolved_at = datetime.utcnow()

    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Ticket updated successfully!', 'success')
    return redirect(url_for('ticket_detail', ticket_id=ticket.id))

@app.route('/add_comment/<int:ticket_id>', methods=['POST'])
@login_required
def add_comment(ticket_id):
    user = User.query.get(session['user_id'])
    ticket = Ticket.query.get_or_404(ticket_id)

    if user.role == 'user' and ticket.created_by != user.id:
        flash('Permission denied.', 'danger')
        return redirect(url_for('tickets'))

    if user.role == 'team_leader' and ticket.team != user.team:
        flash('Permission denied.', 'danger')
        return redirect(url_for('tickets'))

    comment = Comment(
        ticket_id=ticket_id,
        author=user.full_name,
        author_id=user.id,
        content=request.form['content'],
        is_internal=request.form.get('is_internal') == 'on' and user.role in ['admin', 'agent', 'team_leader']
    )
    db.session.add(comment)
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Comment added!', 'success')
    return redirect(url_for('ticket_detail', ticket_id=ticket_id))

@app.route('/delete_ticket/<int:ticket_id>', methods=['POST'])
@admin_required
def delete_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    db.session.delete(ticket)
    db.session.commit()
    flash('Ticket deleted successfully!', 'success')
    return redirect(url_for('tickets'))

# ==================== MY TICKETS (For Users to see assigned tickets) ====================

@app.route('/my_tickets')
@login_required
def my_tickets():
    user = User.query.get(session['user_id'])

    # Show tickets assigned to this user
    assigned_tickets = Ticket.query.filter_by(assigned_to_id=user.id).order_by(Ticket.created_at.desc()).all()

    # Show tickets created by this user
    created_tickets = Ticket.query.filter_by(created_by=user.id).order_by(Ticket.created_at.desc()).all()

    return render_template('my_tickets.html', 
                         assigned_tickets=assigned_tickets, 
                         created_tickets=created_tickets,
                         user=user)

# ==================== MY TEAM (For Team Leaders) ====================

@app.route('/my_team')
@team_leader_required
def my_team():
    user = User.query.get(session['user_id'])

    # Get team members
    team_members = User.query.filter_by(team=user.team, is_active=True).all()

    # Get team tickets
    team_tickets = Ticket.query.filter_by(team=user.team).order_by(Ticket.created_at.desc()).all()

    # Stats
    team_stats = {
        'total': len(team_tickets),
        'open': len([t for t in team_tickets if t.status == 'Open']),
        'in_progress': len([t for t in team_tickets if t.status == 'In Progress']),
        'resolved': len([t for t in team_tickets if t.status == 'Resolved']),
        'closed': len([t for t in team_tickets if t.status == 'Closed']),
        'members': len(team_members)
    }

    return render_template('my_team.html', 
                         team_members=team_members, 
                         team_tickets=team_tickets,
                         team_stats=team_stats,
                         user=user)

# ==================== USER MANAGEMENT (Admin & Agent & Client) ====================

@app.route('/users')
@login_required
def users():
    current = User.query.get(session['user_id'])

    if current.role == 'admin':
        users = User.query.all()
    elif current.role == 'agent':
        users = User.query.filter_by(role='user').all()
    elif current.role == 'team_leader':
        users = User.query.filter_by(team=current.team).all()
    else:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    return render_template('users.html', users=users)

@app.route('/add_user', methods=['POST'])
@login_required
def add_user():
    current = User.query.get(session['user_id'])

    # Only admin, agent, and team_leader can add users
    if current.role not in ['admin', 'agent', 'team_leader']:
        flash('You do not have permission to add users.', 'danger')
        return redirect(url_for('users'))

    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    role = request.form.get('role', 'user')
    team = request.form.get('team', '')

    # Role restrictions
    if current.role == 'agent' and role != 'user':
        flash('Agents can only create regular users.', 'danger')
        return redirect(url_for('users'))

    if current.role == 'team_leader':
        role = 'user'
        team = current.team  # Force team leader's team

    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('users'))

    if User.query.filter_by(email=email).first():
        flash('Email already registered.', 'danger')
        return redirect(url_for('users'))

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        full_name=full_name,
        role=role,
        team=team
    )
    db.session.add(user)
    db.session.commit()
    flash(f'User {username} created successfully!', 'success')
    return redirect(url_for('users'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    current = User.query.get(session['user_id'])
    user = User.query.get_or_404(user_id)

    # Permission checks
    if current.role not in ['admin', 'agent', 'team_leader']:
        flash('You do not have permission to delete users.', 'danger')
        return redirect(url_for('users'))

    if current.role == 'agent' and user.role != 'user':
        flash('Agents can only delete regular users.', 'danger')
        return redirect(url_for('users'))

    if current.role == 'team_leader' and (user.team != current.team or user.role != 'user'):
        flash('You can only delete users from your team.', 'danger')
        return redirect(url_for('users'))

    if user.id == session['user_id']:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('users'))

    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} deleted successfully!', 'success')
    return redirect(url_for('users'))

@app.route('/toggle_user/<int:user_id>', methods=['POST'])
@login_required
def toggle_user(user_id):
    current = User.query.get(session['user_id'])
    user = User.query.get_or_404(user_id)

    if current.role not in ['admin', 'agent', 'team_leader']:
        flash('You do not have permission to manage users.', 'danger')
        return redirect(url_for('users'))

    if current.role == 'agent' and user.role != 'user':
        flash('Agents can only manage regular users.', 'danger')
        return redirect(url_for('users'))

    if current.role == 'team_leader' and (user.team != current.team or user.role != 'user'):
        flash('You can only manage users from your team.', 'danger')
        return redirect(url_for('users'))

    if user.id == session['user_id']:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('users'))

    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {user.username} {"activated" if user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('users'))

@app.route('/change_role/<int:user_id>', methods=['POST'])
@admin_required
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ['admin', 'agent', 'team_leader', 'user']:
        user.role = new_role
        db.session.commit()
        flash(f'Role updated to {new_role}.', 'success')
    return redirect(url_for('users'))

# ==================== API ENDPOINTS ====================

@app.route('/api/stats')
@login_required
def api_stats():
    user = User.query.get(session['user_id'])
    query = Ticket.query
    if user.role == 'user':
        query = query.filter_by(created_by=user.id)
    elif user.role == 'team_leader':
        query = query.filter_by(team=user.team)

    return jsonify({
        'total': query.count(),
        'open': query.filter_by(status='Open').count(),
        'in_progress': query.filter_by(status='In Progress').count(),
        'resolved': query.filter_by(status='Resolved').count(),
        'closed': query.filter_by(status='Closed').count()
    })

@app.route('/api/tickets')
@login_required
def api_tickets():
    user = User.query.get(session['user_id'])
    query = Ticket.query
    if user.role == 'user':
        query = query.filter_by(created_by=user.id)
    elif user.role == 'team_leader':
        query = query.filter_by(team=user.team)

    tickets = query.all()
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'status': t.status,
        'priority': t.priority,
        'category': t.category,
        'requester': t.requester_name,
        'assigned_to': t.assigned_to,
        'closed_by': t.closed_by,
        'closed_at': t.closed_at.isoformat() if t.closed_at else None,
        'created_at': t.created_at.isoformat()
    } for t in tickets])

# ==================== INIT ====================

with app.app_context():
    db.create_all()

    if not User.query.first():
        default_users = [
            User(username='admin', email='admin@ticketsystem.com',
                 password_hash=generate_password_hash('admin123'),
                 full_name='System Administrator', role='admin'),
            User(username='ibrahim', email='shawady6@gmail.com',
                 password_hash=generate_password_hash('password123'),
                 full_name='Ibrahim Elshawady', role='admin'),
            User(username='agent1', email='agent@company.com',
                 password_hash=generate_password_hash('agent123'),
                 full_name='IT Support Agent', role='agent'),
            User(username='leader1', email='leader@company.com',
                 password_hash=generate_password_hash('leader123'),
                 full_name='Team Leader', role='team_leader', team='IT'),
            User(username='user1', email='user1@company.com',
                 password_hash=generate_password_hash('user123'),
                 full_name='Regular User', role='user', team='IT')
        ]
        for user in default_users:
            db.session.add(user)
        db.session.commit()
        print("Default users created!")

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true', host='0.0.0.0', port=5000)
