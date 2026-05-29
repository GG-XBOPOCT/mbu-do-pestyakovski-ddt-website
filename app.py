from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_db, init_db, seed_data

app = Flask(__name__)
app.secret_key = 'pestyaki-ddt-secret'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        project_id = request.form.get('project_id') or None

        if name and email and message:
            conn = get_db()
            conn.execute(
                'INSERT INTO inquiries (name, email, message, created_at, project_id) VALUES (?, ?, ?, ?, ?)',
                (name, email, message, datetime.now().strftime('%Y-%m-%d'), project_id)
            )
            conn.commit()
            conn.close()
            flash('✅ Спасибо! Заявка отправлена.', 'success')
        else:
            flash('❌ Заполните все поля.', 'danger')
        return redirect(url_for('index') + '#contact')

    conn = get_db()
    projects = conn.execute('SELECT * FROM projects').fetchall()
    news = conn.execute('''
        SELECT news.*, projects.title as proj_title 
        FROM news LEFT JOIN projects ON news.project_id = projects.id 
        ORDER BY news.date DESC
    ''').fetchall()
    partners = conn.execute('''
        SELECT partners.*, projects.title as proj_title 
        FROM partners LEFT JOIN projects ON partners.project_id = projects.id
    ''').fetchall()
    conn.close()

    social = {
        'site': 'https://ivobr.ru/mouopestyaki/ddt/',
        'vk': 'https://vk.com/public218228307',
        'email': 'mailto:pesddt@yandex.ru'
    }

    return render_template('index.html', projects=projects, news=news, partners=partners, social=social)


if __name__ == '__main__':
    init_db()
    seed_data()
    app.run(debug=True)