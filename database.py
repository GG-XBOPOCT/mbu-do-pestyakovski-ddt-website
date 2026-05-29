import sqlite3

DB = 'volunteer.db'


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        image TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        date TEXT,
        project_id INTEGER,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS partners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        website TEXT,
        project_id INTEGER,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS inquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT,
        project_id INTEGER,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    )''')

    conn.commit()
    conn.close()


def seed_data():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM projects')
    if c.fetchone()[0] == 0:
        c.executemany('INSERT INTO projects (title, description) VALUES (?, ?)', [
            ('Помощь детям', 'Выезды в детские дома с играми и мастер-классами.'),
            ('Экология', 'Уборка территорий и посадка деревьев в Пестяках.'),
            ('Забота о пожилых', 'Помощь пенсионерам: продукты, уборка, общение.')
        ])
        c.executemany('INSERT INTO news (title, content, date, project_id) VALUES (?, ?, ?, ?)', [
            ('Набор волонтёров', 'Приглашаем школьников и студентов!', '2025-05-20', None),
            ('Акция «Чистый берег»', 'Убрали территорию у озера. Спасибо!', '2025-05-10', 2),
            ('Концерт ко Дню защиты детей', 'Праздничная программа от воспитанников ДДТ.', '2025-06-01', 1)
        ])
        c.executemany('INSERT INTO partners (name, website, project_id) VALUES (?, ?, ?)', [
            ('Администрация района', 'https://pestyakovskij-r24.gosweb.gosuslugi.ru/', None),  # Обновленная ссылка
            ('Библиотека им. Пушкина', 'http://lib-pestyaki.ivn.muzkult.ru/', 1),  # Обновленная ссылка
            ('Дом культуры', 'https://pestyakovskij-r24.gosweb.gosuslugi.ru/spravochnik/kontsertnye-zaly/', 3)
        ])
    conn.commit()
    conn.close()