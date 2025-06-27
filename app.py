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
    app.run(port="5006", debug=True)
