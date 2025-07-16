from flask import redirect, url_for, request
from flask import Flask, send_from_directory, render_template
from flask_restx import Api
from routes.materi_routes import api as materi_ns
from routes.storytelling_routes import api as storytelling_ns
from routes.auth_routes import auth_ns
from routes.achievement_routes import api as achievement_ns
from routes.materi_progress_routes import api as progress_ns
from routes.storytelling_routes import api as storytelling_ns
from routes.storytelling_progress_routes import api as storytelling_progress_ns
from routes.storytelling_progress_join import api as storytelling_progress_combined_ns
from routes.soal import api as soal_ns
from routes.soal_crud import api as api_soal_crud
from routes.user_achievement import achievement_ns
from routes.musik import api as musik_ns
from routes.map_route import api as map_api
from db import get_connection


app = Flask(__name__)
api = Api(app, title="Materi API", version="1.0",
          description="API untuk manajemen materi dan file PDF")


@app.route('/user-progress/<int:user_id>')
def user_progress_view(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM user_progress
        WHERE user_id = %s
        ORDER BY tile_id DESC, updated_at DESC
    """, (user_id,))
    rows = cursor.fetchall()

    # Ambil hanya 1 data terakhir per tile_id
    seen_tile_ids = set()
    progress = []
    for row in rows:
        if row['tile_id'] not in seen_tile_ids:
            progress.append(row)
            seen_tile_ids.add(row['tile_id'])

    cursor.close()
    conn.close()
    return render_template("user_progress.html", user_id=user_id, progress=progress)


@app.route('/user-progress')
def semua_user_progress_view():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT up.*, u.name
        FROM user_progress up
        INNER JOIN (
            SELECT user_id, MAX(updated_at) AS max_updated
            FROM user_progress
            GROUP BY user_id
        ) latest ON up.user_id = latest.user_id AND up.updated_at = latest.max_updated
        JOIN users u ON u.id = up.user_id
        ORDER BY up.updated_at DESC
    """)
    progress = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("user_progress.html", progress=progress)


@app.route('/user-progress/<int:user_id>/tambah-nyawa/<int:progress_id>', methods=['POST'])
def tambah_nyawa(user_id, progress_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT lives FROM user_progress WHERE id = %s", (progress_id,))
    current = cursor.fetchone()
    if current and current[0] < 3:
        cursor.execute(
            "UPDATE user_progress SET lives = lives + 1 WHERE id = %s", (progress_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('semua_user_progress_view'))


@app.route('/update-progress', methods=['POST'])
def update_progress():
    data = request.get_json()
    user_id = data.get('user_id')
    tile_id = data.get('tile_id')
    status = data.get('status')
    lives = data.get('lives')

    if not all([user_id, tile_id, status, lives]):
        return {'success': False, 'message': 'Data tidak lengkap'}, 400

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE user_progress
            SET status = %s, lives = %s
            WHERE user_id = %s AND tile_id = %s
        """, (status, lives, user_id, tile_id))
        conn.commit()
        return {'success': True}
    except Exception as e:
        conn.rollback()
        return {'success': False, 'message': str(e)}, 500
    finally:
        cursor.close()
        conn.close()


@app.route('/user-progress/<int:user_id>/unlock/<int:progress_id>', methods=['POST'])
def unlock_tile(user_id, progress_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE user_progress SET status = 'unlocked' WHERE id = %s", (progress_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('semua_user_progress_view'))


@app.route('/soal-crud-view')
def soal_crud_view():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM soal")
    soal = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("soal_crud.html", soal=soal, active_page="soal")


@app.route('/uploads/<path:filename>')
def serve_pdf(filename):
    return send_from_directory('uploads', filename)


api.add_namespace(api_soal_crud, path="/api/soal-crud")
# Registrasi namespace
api.add_namespace(materi_ns, path="/api/materi")
api.add_namespace(storytelling_ns, path='/api/storytelling')
api.add_namespace(auth_ns, path='/api/auth')
api.add_namespace(achievement_ns, path='/api/achievement')
api.add_namespace(progress_ns, path='/materi-progress')
api.add_namespace(storytelling_ns, path='/storytelling')
# api.add_namespace(storytelling_progress_ns, path='/api/storytelling-progress')
api.add_namespace(storytelling_progress_combined_ns,
                  path='/api/storytelling-progress')
api.add_namespace(map_api, path='/api/map')
api.add_namespace(soal_ns, path='/api/soal')
api.add_namespace(achievement_ns, path='/api/user')
api.add_namespace(musik_ns, path="/api/musik")
if __name__ == '__main__':
    app.run(port="5006", host="0.0.0.0", debug=True)
