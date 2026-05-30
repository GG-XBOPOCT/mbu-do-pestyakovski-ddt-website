from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Пожалуйста, войдите в админ-панель', 'warning')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------- Авторизация ----------
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Вы успешно вошли', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('Вы вышли из админ-панели', 'info')
    return redirect(url_for('admin.login'))

# ---------- Главная админки ----------
@admin_bp.route('/')
@login_required
def dashboard():
    conn = get_db()
    projects_count = conn.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
    news_count = conn.execute('SELECT COUNT(*) FROM news').fetchone()[0]
    partners_count = conn.execute('SELECT COUNT(*) FROM partners').fetchone()[0]
    inquiries_count = conn.execute('SELECT COUNT(*) FROM inquiries').fetchone()[0]
    conn.close()
    return render_template('admin/dashboard.html',
                           projects_count=projects_count,
                           news_count=news_count,
                           partners_count=partners_count,
                           inquiries_count=inquiries_count)

# ---------- Проекты ----------
@admin_bp.route('/projects')
@login_required
def projects():
    conn = get_db()
    projects = conn.execute('SELECT * FROM projects ORDER BY id').fetchall()
    conn.close()
    return render_template('admin/projects.html', projects=projects)

@admin_bp.route('/project/add', methods=['GET', 'POST'])
@login_required
def add_project():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        conn = get_db()
        conn.execute('INSERT INTO projects (title, description) VALUES (?, ?)',
                     (title, description))
        conn.commit()
        conn.close()
        flash('Проект добавлен', 'success')
        return redirect(url_for('admin.projects'))
    return render_template('admin/project_form.html', project=None)

@admin_bp.route('/project/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_project(id):
    conn = get_db()
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        conn.execute('UPDATE projects SET title=?, description=? WHERE id=?',
                     (title, description, id))
        conn.commit()
        conn.close()
        flash('Проект обновлён', 'success')
        return redirect(url_for('admin.projects'))
    project = conn.execute('SELECT * FROM projects WHERE id=?', (id,)).fetchone()
    conn.close()
    return render_template('admin/project_form.html', project=project)

@admin_bp.route('/project/delete/<int:id>')
@login_required
def delete_project(id):
    conn = get_db()
    news = conn.execute('SELECT COUNT(*) FROM news WHERE project_id=?', (id,)).fetchone()[0]
    partners = conn.execute('SELECT COUNT(*) FROM partners WHERE project_id=?', (id,)).fetchone()[0]
    if news > 0 or partners > 0:
        flash('Нельзя удалить проект: есть связанные новости или партнёры', 'danger')
    else:
        conn.execute('DELETE FROM projects WHERE id=?', (id,))
        conn.commit()
        flash('Проект удалён', 'success')
    conn.close()
    return redirect(url_for('admin.projects'))

# ---------- Новости ----------
@admin_bp.route('/news')
@login_required
def news():
    conn = get_db()
    news = conn.execute('''
        SELECT news.*, projects.title as project_title
        FROM news
        LEFT JOIN projects ON news.project_id = projects.id
        ORDER BY news.date DESC
    ''').fetchall()
    conn.close()
    return render_template('admin/news.html', news=news)

@admin_bp.route('/news/add', methods=['GET', 'POST'])
@login_required
def add_news():
    conn = get_db()
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        date = request.form.get('date')
        project_id = request.form.get('project_id') or None
        conn.execute('INSERT INTO news (title, content, date, project_id) VALUES (?, ?, ?, ?)',
                     (title, content, date, project_id))
        conn.commit()
        conn.close()
        flash('Новость добавлена', 'success')
        return redirect(url_for('admin.news'))
    projects = conn.execute('SELECT id, title FROM projects').fetchall()
    conn.close()
    return render_template('admin/news_form.html', news=None, projects=projects)

@admin_bp.route('/news/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    conn = get_db()
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        date = request.form.get('date')
        project_id = request.form.get('project_id') or None
        conn.execute('UPDATE news SET title=?, content=?, date=?, project_id=? WHERE id=?',
                     (title, content, date, project_id, id))
        conn.commit()
        conn.close()
        flash('Новость обновлена', 'success')
        return redirect(url_for('admin.news'))
    news_item = conn.execute('SELECT * FROM news WHERE id=?', (id,)).fetchone()
    projects = conn.execute('SELECT id, title FROM projects').fetchall()
    conn.close()
    return render_template('admin/news_form.html', news=news_item, projects=projects)

@admin_bp.route('/news/delete/<int:id>')
@login_required
def delete_news(id):
    conn = get_db()
    conn.execute('DELETE FROM news WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Новость удалена', 'success')
    return redirect(url_for('admin.news'))

# ---------- Партнёры ----------
@admin_bp.route('/partners')
@login_required
def partners():
    conn = get_db()
    partners = conn.execute('''
        SELECT partners.*, projects.title as project_title
        FROM partners
        LEFT JOIN projects ON partners.project_id = projects.id
    ''').fetchall()
    conn.close()
    return render_template('admin/partners.html', partners=partners)

@admin_bp.route('/partner/add', methods=['GET', 'POST'])
@login_required
def add_partner():
    conn = get_db()
    if request.method == 'POST':
        name = request.form.get('name')
        website = request.form.get('website')
        project_id = request.form.get('project_id') or None
        conn.execute('INSERT INTO partners (name, website, project_id) VALUES (?, ?, ?)',
                     (name, website, project_id))
        conn.commit()
        conn.close()
        flash('Партнёр добавлен', 'success')
        return redirect(url_for('admin.partners'))
    projects = conn.execute('SELECT id, title FROM projects').fetchall()
    conn.close()
    return render_template('admin/partner_form.html', partner=None, projects=projects)

@admin_bp.route('/partner/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_partner(id):
    conn = get_db()
    if request.method == 'POST':
        name = request.form.get('name')
        website = request.form.get('website')
        project_id = request.form.get('project_id') or None
        conn.execute('UPDATE partners SET name=?, website=?, project_id=? WHERE id=?',
                     (name, website, project_id, id))
        conn.commit()
        conn.close()
        flash('Партнёр обновлён', 'success')
        return redirect(url_for('admin.partners'))
    partner = conn.execute('SELECT * FROM partners WHERE id=?', (id,)).fetchone()
    projects = conn.execute('SELECT id, title FROM projects').fetchall()
    conn.close()
    return render_template('admin/partner_form.html', partner=partner, projects=projects)

@admin_bp.route('/partner/delete/<int:id>')
@login_required
def delete_partner(id):
    conn = get_db()
    conn.execute('DELETE FROM partners WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Партнёр удалён', 'success')
    return redirect(url_for('admin.partners'))

# ---------- Заявки ----------
@admin_bp.route('/inquiries')
@login_required
def inquiries():
    conn = get_db()
    inquiries = conn.execute('''
        SELECT inquiries.*, projects.title as project_title
        FROM inquiries
        LEFT JOIN projects ON inquiries.project_id = projects.id
        ORDER BY inquiries.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('admin/inquiries.html', inquiries=inquiries)

@admin_bp.route('/inquiry/delete/<int:id>')
@login_required
def delete_inquiry(id):
    conn = get_db()
    conn.execute('DELETE FROM inquiries WHERE id=?', (id,))
    conn.commit()
    conn.close()
    flash('Заявка удалена', 'success')
    return redirect(url_for('admin.inquiries'))