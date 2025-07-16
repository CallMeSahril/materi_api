from flask import request, send_from_directory
from flask_restx import Namespace, Resource, fields
from db import get_connection
from config import UPLOAD_FOLDER
import hashlib
import mysql.connector

auth_ns = Namespace('auth', description='User Authentication')

# === MODELS ===
register_model = auth_ns.model('Register', {
    'name': fields.String(required=True),
    'email': fields.String(required=True),
    'password': fields.String(required=True),
})

login_model = auth_ns.model('Login', {
    'email': fields.String(required=True),
    'password': fields.String(required=True),
})


@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(register_model)
    def post(self):
        data = request.json
        name = data['name']
        email = data['email']
        password = data['password']
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            print(f"📥 Mencoba registrasi: {name}, {email}")

            # Cek apakah email sudah terdaftar
            cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cursor.fetchone():
                print("⚠️ Email sudah terdaftar!")
                return {'message': 'Email already exists'}, 400

            # Tambah user baru
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                (name, email, hashed_pw)
            )
            user_id = cursor.lastrowid
            print(f"✅ User berhasil ditambahkan dengan ID: {user_id}")

            # --- Inisialisasi progres ---
            cursor.execute("SELECT id FROM storytelling")
            stories = cursor.fetchall()
            print(f"🔹 Storytelling ditemukan: {len(stories)}")
            for (story_id,) in stories:
                cursor.execute("INSERT INTO storytelling_progress (user_id, storytelling_id, is_watched) VALUES (%s, %s, %s)",
                               (user_id, story_id, False))

            cursor.execute("SELECT id FROM materi")
            materi = cursor.fetchall()
            print(f"🔹 Materi ditemukan: {len(materi)}")
            for (materi_id,) in materi:
                cursor.execute("INSERT INTO materi_progress (user_id, materi_id, is_watched, is_completed) VALUES (%s, %s, %s, %s)",
                               (user_id, materi_id, False, False))

            # cursor.execute("SELECT id FROM quiz_master")
            # quizzes = cursor.fetchall()
            # print(f"🔹 Quiz ditemukan: {len(quizzes)}")
            # for (quiz_id,) in quizzes:
            #     cursor.execute("INSERT INTO quiz_progress (user_id, quiz_id, is_passed) VALUES (%s, %s, %s)",
            #                    (user_id, quiz_id, False))

            cursor.execute("SELECT id FROM achievement_master")
            achvs = cursor.fetchall()
            print(f"🔹 Achievement ditemukan: {len(achvs)}")
            for (achv_id,) in achvs:
                cursor.execute("INSERT INTO achievement_progress (user_id, achievement_id, is_unlocked) VALUES (%s, %s, %s)",
                               (user_id, achv_id, False))

            # === Cek tile awal ===
            cursor.execute(
                "SELECT id FROM tiles WHERE position = 0 ORDER BY id ASC LIMIT 1")
            first_tile = cursor.fetchone()
            print(f"🧩 Tile pertama: {first_tile}")

            if first_tile:
                cursor.execute("""
                    INSERT INTO user_progress (user_id, tile_id, status)
                    VALUES (%s, %s, %s)
                """, (user_id, first_tile[0], 'unlocked'))
                print(f"✅ Tile {first_tile[0]} di-unlock untuk user {user_id}")

            conn.commit()
            return {'message': 'User registered successfully', 'user_id': user_id}, 201

        except mysql.connector.Error as e:
            conn.rollback()
            print(f"❌ Database error: {e}")
            return {'message': 'Database error: ' + str(e)}, 500

        finally:
            cursor.close()
            conn.close()


# === LOGIN ROUTE ===
@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    def post(self):
        data = request.json
        email = data['email']
        password = data['password']
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT id, name, email FROM users WHERE email = %s AND password = %s",
                (email, hashed_pw)
            )
            user = cursor.fetchone()

            if user:
                return {'message': 'Login success', 'user': user}, 200
            else:
                return {'message': 'Invalid credentials'}, 401

        except mysql.connector.Error as e:
            return {'message': 'Database error: ' + str(e)}, 500

        finally:
            cursor.close()
            conn.close()
