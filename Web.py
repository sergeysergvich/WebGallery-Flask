import os
import uuid
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'static/iMAGE'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

FAVORITES_FILE = 'favorites.json'


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_favorites():
    """Получить список избранных изображений"""
    if os.path.exists(FAVORITES_FILE):
        try:
            with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_favorites(favorites):
    """Сохранить список избранных изображений"""
    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)


def scan_directory(directory):
    tree = []
    for root, dirs, files in os.walk(directory):
        current_folder = {
            'name': os.path.basename(root),
            'path': root,
            'images': [os.path.join(os.path.basename(root), file).replace("\\", "/")
                       for file in files if file.lower().endswith(('jpg', 'jpeg', 'png', 'gif'))],
            'subfolders': []
        }
        for dir in dirs:
            current_folder['subfolders'].append(scan_directory(os.path.join(root, dir)))
        tree.append(current_folder)
    return tree


@app.route('/')
def index():
    directory = 'static/iMAGE'
    tree = scan_directory(directory)
    favorites = get_favorites()
    return render_template('index.html', gallery_data=tree, favorites=favorites)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Файл не выбран', 'error')
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        flash('Файл не выбран', 'error')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # Создаем уникальное имя файла
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"

        # Сохраняем в основную папку
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(save_path)

        flash(f'Изображение "{filename}" успешно загружено!', 'success')
    else:
        flash('Недопустимый формат файла. Разрешены: PNG, JPG, JPEG, GIF', 'error')

    return redirect(url_for('index'))


@app.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    image_path = request.form.get('image_path')
    action = request.form.get('action')  # 'add' или 'remove'

    favorites = get_favorites()

    if action == 'add' and image_path not in favorites:
        favorites.append(image_path)
        save_favorites(favorites)
        return jsonify({'success': True, 'action': 'added'})
    elif action == 'remove' and image_path in favorites:
        favorites.remove(image_path)
        save_favorites(favorites)
        return jsonify({'success': True, 'action': 'removed'})

    return jsonify({'success': False, 'error': 'Invalid action'})


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)