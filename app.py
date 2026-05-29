from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_db, init_db, seed_data
import requests
import json
import re
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = 'pestyaki-ddt-secret'


def fetch_dobro_news():
    """
    Парсит три последние новости со страницы https://dobro.ru/organizations/150278/feed
    Использует встроенный JSON-объект __NEXT_DATA__.
    Возвращает список словарей: [{'title': ..., 'date': ..., 'link': ..., 'description': ..., 'image': ...}, ...]
    """
    news_list = []
    url = 'https://dobro.ru/organizations/150278/feed'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Находим скрипт с id="__NEXT_DATA__"
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        if not next_data_script:
            print("Не найден скрипт __NEXT_DATA__")
            return []

        # Парсим JSON
        data = json.loads(next_data_script.string)

        # Ищем посты в структуре dehydratedState
        # Обычно они лежат в props.pageProps.dehydratedState.queries[0].state.data.pages[0].data
        queries = data.get('props', {}).get('pageProps', {}).get('dehydratedState', {}).get('queries', [])
        posts_data = None
        for query in queries:
            if query.get('state', {}).get('data', {}).get('pages'):
                pages = query['state']['data']['pages']
                if pages and 'data' in pages[0]:
                    posts_data = pages[0]['data']
                    break

        if not posts_data:
            print("Не удалось извлечь посты из JSON")
            return []

        # Берём первые 3 поста (самые свежие)
        for post in posts_data[:3]:
            # Извлекаем ID поста для формирования ссылки
            post_id = post.get('id')
            link = f'https://dobro.ru/organizations/150278/feed?postId={post_id}' if post_id else '#'

            # Дата
            created_at = post.get('createdAt', '')
            # Преобразуем "2026-05-05T08:03:35+03:00" -> "2026-05-05"
            if created_at:
                date_iso = created_at[:10]
            else:
                date_iso = ''

            # Описание – HTML-текст, очищаем от тегов
            raw_description = post.get('description', '')
            # Удаляем HTML-теги (включая <br> заменяем на пробел)
            clean_description = re.sub(r'<br\s*/?>', ' ', raw_description)
            clean_description = re.sub(r'<[^>]+>', '', clean_description)
            # Убираем лишние пробелы
            clean_description = ' '.join(clean_description.split())
            # Ограничиваем длину для карточки (например, 300 символов)
            short_description = clean_description[:300] + '…' if len(clean_description) > 300 else clean_description

            # Заголовок – можно взять первые 100 символов описания или вырезать первую фразу
            # Лучше: первое предложение до точки или до первого перевода строки
            title = clean_description.split('.')[0].strip()
            if len(title) > 100:
                title = title[:97] + '…'

            # Изображение
            image = post.get('fileS3Link', '')

            news_list.append({
                'title': title,
                'date': date_iso,
                'link': link,
                'description': short_description,
                'image': image
            })

    except Exception as e:
        print(f"Ошибка при парсинге dobro.ru: {e}")

    return news_list


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

    # Новости из базы данных
    db_news = conn.execute('''
        SELECT news.*, projects.title as proj_title 
        FROM news LEFT JOIN projects ON news.project_id = projects.id 
        ORDER BY news.date DESC
    ''').fetchall()

    # Парсим новости с dobro.ru
    dobro_news = fetch_dobro_news()

    # Объединяем: сначала свои новости, потом с dobro.ru
    all_news = list(db_news) + dobro_news

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

    return render_template('index.html',
                           projects=projects,
                           news=all_news,
                           partners=partners,
                           social=social,
                           dobro_feed_url='https://dobro.ru/organizations/150278/feed')


if __name__ == '__main__':
    init_db()
    seed_data()
    app.run(debug=True)