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


@auth_ns.route('/change-password/<int:user_id>')
class ChangePassword(Resource):
    def put(self, user_id):
        data = request.json
        old_pw = data.get('old_password')
        new_pw = data.get('new_password')
        confirm_pw = data.get('confirm_password')

        print(f"🔐 Request ubah password user_id={user_id}")
        print(
            f"📥 Input: old_pw={'*' * len(old_pw) if old_pw else None}, new_pw={'*' * len(new_pw) if new_pw else None}")

        if not old_pw or not new_pw or not confirm_pw:
            print("⚠️ Gagal: Field kosong")
            return {'message': 'Semua field wajib diisi'}, 400

        if new_pw != confirm_pw:
            print("⚠️ Gagal: Konfirmasi password tidak cocok")
            return {'message': 'Konfirmasi password tidak cocok'}, 400

        conn = get_connection()
        cursor = conn.cursor()

        try:
            old_hashed = hashlib.sha256(old_pw.encode()).hexdigest()
            cursor.execute(
                "SELECT password FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()

            if not result:
                print("❌ Gagal: User tidak ditemukan")
                return {'message': 'User tidak ditemukan'}, 404

            if result[0] != old_hashed:
                print("❌ Gagal: Password lama salah")
                return {'message': 'Password lama salah'}, 401

            new_hashed = hashlib.sha256(new_pw.encode()).hexdigest()
            cursor.execute(
                "UPDATE users SET password = %s WHERE id = %s", (new_hashed, user_id))
            conn.commit()

            print("✅ Password berhasil diubah")
            return {'message': 'Password berhasil diubah'}, 200

        except mysql.connector.Error as e:
            conn.rollback()
            print(f"❌ Database Error: {str(e)}")
            return {'message': 'Database error: ' + str(e)}, 500

        finally:
            cursor.close()
            conn.close()


@auth_ns.route('/delete/<int:user_id>')
class ForceDeleteUser(Resource):
    def delete(self, user_id):
        print(
            f"🗑️ Permintaan hapus user_id={user_id} dan semua relasi terkait")

        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Hapus seluruh relasi
            tables = [
                "storytelling_progress",
                "materi_progress",
                "quiz_progress",
                "achievement_progress",
                "user_progress"
            ]

            for table in tables:
                cursor.execute(
                    f"DELETE FROM {table} WHERE user_id = %s", (user_id,))
                print(f"✔️ Data dari {table} dihapus")

            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            print(f"✅ User ID {user_id} berhasil dihapus dari tabel users")

            conn.commit()
            return {'message': f'User ID {user_id} dan seluruh datanya berhasil dihapus'}, 200

        except mysql.connector.Error as e:
            conn.rollback()
            print(f"❌ Database Error saat hapus user: {str(e)}")
            return {'message': 'Database error: ' + str(e)}, 500

        finally:
            cursor.close()
            conn.close()
