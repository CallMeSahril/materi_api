from flask import request
from flask_restx import Namespace, Resource, fields
from db import get_connection

api = Namespace(
    'Soal', description='Soal berdasarkan Tile dan Jawaban Pengguna')

# ====== SCHEMA =======
soal_model = api.model('Soal', {
    'id': fields.Integer,
    'pertanyaan': fields.String,
    'pilihan_a': fields.String,
    'pilihan_b': fields.String,
    'pilihan_c': fields.String,
    'pilihan_d': fields.String,
    'gambar': fields.String,
    'gambar_url': fields.String,
    'gambar_a_url': fields.String,
    'gambar_b_url': fields.String,
    'gambar_c_url': fields.String,
    'gambar_d_url': fields.String,
})

response_model = api.model('SoalResponse', {
    'soal': fields.Nested(soal_model),
    'page': fields.Integer,
    'total_soal': fields.Integer,
    'lives': fields.Integer,
    'status': fields.String,
})

jawaban_model = api.model('JawabanInput', {
    'user_id': fields.Integer(required=True, description='ID Pengguna'),
    'tile_id': fields.Integer(required=True, description='ID Tile'),
    'soal_id': fields.Integer(required=True, description='ID Soal'),
    'jawaban': fields.String(required=True, description='Jawaban yang dipilih'),
})
# ====== ENDPOINT: GET SOAL BY TILE =======


# @api.route('/<int:tile_id>')
# class SoalByTile(Resource):
#     @api.doc(params={'user_id': 'ID pengguna', 'page': 'Soal keberapa'})
#     @api.marshal_with(response_model)
#     def get(self, tile_id):
#         user_id = request.args.get('user_id', type=int)
#         page = request.args.get('page', default=1, type=int)

#         print(
#             f"[DEBUG] GET soal - tile_id: {tile_id}, user_id: {user_id}, page: {page}")

#         conn = get_connection()
#         cursor = conn.cursor(dictionary=True)

#         cursor.execute("""
#             SELECT s.*
#             FROM soal s
#             JOIN kumpulan_soal ks ON s.kumpulan_soal_id = ks.id
#             JOIN tiles t ON t.kumpulan_soal_id = ks.id
#             WHERE t.id = %s
#             ORDER BY s.id ASC
#         """, (tile_id,))
#         all_soal = cursor.fetchall()
#         total = len(all_soal)
#         print(f"[DEBUG] Total soal ditemukan: {total}")

#         if total == 0 or page < 1 or page > total:
#             print(f"[DEBUG] Halaman tidak valid")
#             return {'soal': None, 'page': page, 'total_soal': total, 'lives': 0, 'status': 'invalid'}, 404

#         soal = all_soal[page - 1]
#         print(f"[DEBUG] Soal terpilih: {soal['id']}")

#         host_url = "https://nngwj5fn-5006.asse.devtunnels.ms/"
#         soal['gambar_url'] = f"{host_url}/static/uploads/{soal['gambar']}" if soal.get(
#             'gambar') else ''
#         soal['gambar_a_url'] = f"{host_url}/static/uploads/{soal['gambar_a']}" if soal.get(
#             'gambar_a') else ''
#         soal['gambar_b_url'] = f"{host_url}/static/uploads/{soal['gambar_b']}" if soal.get(
#             'gambar_b') else ''
#         soal['gambar_c_url'] = f"{host_url}/static/uploads/{soal['gambar_c']}" if soal.get(
#             'gambar_c') else ''
#         soal['gambar_d_url'] = f"{host_url}/static/uploads/{soal['gambar_d']}" if soal.get(
#             'gambar_d') else ''

#         cursor.execute("""
#             SELECT lives FROM user_progress
#             WHERE user_id = %s AND tile_id = %s
#         """, (user_id, tile_id))
#         result = cursor.fetchone()
#         lives = result['lives'] if result else 3
#         print(f"[DEBUG] Lives user: {lives}")

#         if tile_id in (16, 32, 48, 64):
#             print("[DEBUG] Mencatat pencapaian langsung untuk tile istimewa")
#             cursor.execute("""
#                         INSERT INTO user_achievement (user_id, tile_id, achievement_name)
#                         VALUES (%s, %s, %s)
#                         ON DUPLICATE KEY UPDATE achievement_name = VALUES(achievement_name)
#                     """, (user_id, tile_id, f"Achievement Langsung untuk tile {tile_id}"))

#         cursor.close()
#         conn.close()

#         return {
#             'soal': soal,
#             'page': page,
#             'total_soal': total,
#             'lives': lives,
#             'status': 'finished' if page == total else 'in_progress'
#         }
@api.route('/<int:tile_id>')
class SoalByTile(Resource):
    @api.doc(params={'user_id': 'ID pengguna', 'page': 'Soal keberapa'})
    @api.marshal_with(response_model)
    def get(self, tile_id):
        user_id = request.args.get('user_id', type=int)
        page = request.args.get('page', default=1, type=int)

        print(
            f"[DEBUG] GET soal - tile_id: {tile_id}, user_id: {user_id}, page: {page}")

        conn = get_connection()
        print("[DEBUG] Database connection established")
        cursor = conn.cursor(dictionary=True)

        print("[DEBUG] Menjalankan query untuk mengambil soal berdasarkan tile")
        cursor.execute("""
            SELECT s.*
            FROM soal s
            JOIN kumpulan_soal ks ON s.kumpulan_soal_id = ks.id
            JOIN tiles t ON t.kumpulan_soal_id = ks.id
            WHERE t.id = %s
            ORDER BY s.id ASC
        """, (tile_id,))
        all_soal = cursor.fetchall()
        total = len(all_soal)
        print(f"[DEBUG] Total soal ditemukan: {total}")

        if tile_id in (16, 32, 48, 64):
            print(
                "[DEBUG] Mendeteksi tile spesial, melakukan pencapaian otomatis dan membuka tile berikutnya")
            cursor.execute("""
                INSERT INTO user_achievement (user_id, tile_id, achievement_name)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE achievement_name = VALUES(achievement_name)
            """, (user_id, tile_id, f"Achievement Langsung untuk tile {tile_id}"))
            print("[DEBUG] Achievement tercatat")

            cursor.execute("""
                INSERT INTO user_progress (user_id, tile_id, lives, status)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE status = VALUES(status)
            """, (user_id, tile_id, 3, 'completed'))
            print("[DEBUG] Menandai tile saat ini sebagai completed")

            cursor.execute(
                "SELECT level_id, position FROM tiles WHERE id = %s", (tile_id,))
            info = cursor.fetchone()
            if info:
                level_id = info['level_id']
                print(
                    f"[DEBUG] Mencari tile berikutnya setelah level {level_id}, posisi {info['position']}")
                cursor.execute("""
                    SELECT id FROM tiles
                    WHERE (level_id > %s OR (level_id = %s AND position > %s))
                    ORDER BY level_id ASC, position ASC
                    LIMIT 1
                """, (level_id, level_id, info['position']))
                next_tile = cursor.fetchone()
                if next_tile:
                    print(
                        f"[DEBUG] Membuka tile berikutnya dengan ID {next_tile['id']}")
                    cursor.execute("""
                        INSERT INTO user_progress (user_id, tile_id, lives, status)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE status = VALUES(status)
                    """, (user_id, next_tile['id'], 3, 'unlocked'))

        if total == 0:
            print(f"[DEBUG] Halaman tidak valid karena tidak ada soal")
            cursor.execute(
                "SELECT lives FROM user_progress WHERE user_id = %s AND tile_id = %s", (user_id, tile_id))
            result = cursor.fetchone()
            lives = result['lives'] if result else 3
            print(f"[DEBUG] Lives saat ini: {lives}")
            cursor.close()
            conn.commit()
            conn.close()
            return {'soal': None, 'page': page, 'total_soal': total, 'lives': lives, 'status': 'empty'}

        if page < 1 or page > total:
            print(f"[DEBUG] Halaman {page} tidak valid (total {total})")
            cursor.close()
            conn.close()
            return {'soal': None, 'page': page, 'total_soal': total, 'lives': 0, 'status': 'invalid'}, 404

        soal = all_soal[page - 1]
        print(f"[DEBUG] Soal terpilih dengan ID: {soal['id']}")

        host_url = "https://nngwj5fn-5006.asse.devtunnels.ms/"
        soal['gambar_url'] = f"{host_url}/static/uploads/{soal['gambar']}" if soal.get(
            'gambar') else ''
        soal['gambar_a_url'] = f"{host_url}/static/uploads/{soal['gambar_a']}" if soal.get(
            'gambar_a') else ''
        soal['gambar_b_url'] = f"{host_url}/static/uploads/{soal['gambar_b']}" if soal.get(
            'gambar_b') else ''
        soal['gambar_c_url'] = f"{host_url}/static/uploads/{soal['gambar_c']}" if soal.get(
            'gambar_c') else ''
        soal['gambar_d_url'] = f"{host_url}/static/uploads/{soal['gambar_d']}" if soal.get(
            'gambar_d') else ''

        cursor.execute(
            "SELECT lives FROM user_progress WHERE user_id = %s AND tile_id = %s", (user_id, tile_id))
        result = cursor.fetchone()
        lives = result['lives'] if result else 3
        print(f"[DEBUG] Lives user: {lives}")

        cursor.close()
        conn.commit()
        conn.close()
        print("[DEBUG] Koneksi database ditutup")

        return {
            'soal': soal,
            'page': page,
            'total_soal': total,
            'lives': lives,
            'status': 'finished' if page == total else 'in_progress'
        }


# @api.expect(jawaban_model)
# @api.route('/jawab')
# class Jawab(Resource):
#     def post(self):
#         data = request.json
#         user_id = data.get('user_id')
#         tile_id = data.get('tile_id')
#         soal_id = data.get('soal_id')
#         jawaban = data.get('jawaban')

#         print(
#             f"[DEBUG] POST jawab - user_id: {user_id}, tile_id: {tile_id}, soal_id: {soal_id}, jawaban: {jawaban}")

#         if not all([user_id, tile_id, soal_id, jawaban]):
#             print("[DEBUG] Data tidak lengkap")
#             return {'message': 'Data tidak lengkap'}, 400

#         conn = get_connection()
#         cursor = conn.cursor(dictionary=True)

#         cursor.execute(
#             "SELECT jawaban_benar FROM soal WHERE id = %s", (soal_id,))
#         soal = cursor.fetchone()
#         if not soal:
#             print("[DEBUG] Soal tidak ditemukan")
#             return {'message': 'Soal tidak ditemukan'}, 404

#         jawaban_benar = soal['jawaban_benar']
#         benar = jawaban.upper() == jawaban_benar.upper()
#         print(f"[DEBUG] Jawaban benar: {jawaban_benar}, User benar: {benar}")

#         cursor.execute(
#             "SELECT * FROM user_progress WHERE user_id = %s AND tile_id = %s", (user_id, tile_id))
#         progress = cursor.fetchone()

#         if not progress:
#             print("[DEBUG] Membuat progress baru")
#             lives = 3
#             status = 'in_progress'
#             cursor.execute("""
#                 INSERT INTO user_progress (user_id, tile_id, status, lives)
#                 VALUES (%s, %s, %s, %s)
#             """, (user_id, tile_id, status, lives))
#         else:
#             lives = progress['lives']
#             status = progress['status']
#             print(
#                 f"[DEBUG] Progress ditemukan - lives: {lives}, status: {status}")
#             if status in ('completed', 'failed'):
#                 return {'correct': True, 'remaining_lives': lives}

#         cursor.execute("""
#             SELECT * FROM jawaban_user
#             WHERE user_id = %s AND tile_id = %s AND soal_id = %s
#         """, (user_id, tile_id, soal_id))
#         existing = cursor.fetchone()
#         if existing:
#             print("[DEBUG] Jawaban sudah pernah dikirim")
#             return {'correct': existing['benar'], 'remaining_lives': lives}

#         if benar:
#             cursor.execute("""
#                 INSERT INTO jawaban_user (user_id, tile_id, soal_id, jawaban, benar)
#                 VALUES (%s, %s, %s, %s, %s)
#             """, (user_id, tile_id, soal_id, jawaban.upper(), benar))
#         else:
#             lives = max(0, lives - 1)
#             print(f"[DEBUG] Jawaban salah, lives berkurang jadi: {lives}")
#             cursor.execute("UPDATE user_progress SET lives = %s WHERE user_id = %s AND tile_id = %s",
#                            (lives, user_id, tile_id))

#         if lives == 0:
#             print("[DEBUG] Lives habis, status gagal")
#             cursor.execute("""
#                 UPDATE user_progress SET status = 'failed'
#                 WHERE user_id = %s AND tile_id = %s
#             """, (user_id, tile_id))
#         else:
#             cursor.execute("""
#                 SELECT COUNT(*) AS total FROM soal
#                 JOIN tiles t ON soal.kumpulan_soal_id = t.kumpulan_soal_id
#                 WHERE t.id = %s
#             """, (tile_id,))
#             total_soal = cursor.fetchone()['total']

#             cursor.execute("""
#                 SELECT COUNT(*) AS answered FROM jawaban_user
#                 WHERE user_id = %s AND tile_id = %s
#             """, (user_id, tile_id))
#             answered = cursor.fetchone()['answered']

#             print(
#                 f"[DEBUG] Total soal: {total_soal}, Sudah dijawab: {answered}")

#             if answered >= total_soal:
#                 # Cek apakah semua jawaban benar
#                 cursor.execute("""
#                     SELECT COUNT(*) AS benar FROM jawaban_user
#                     WHERE user_id = %s AND tile_id = %s AND benar = 1
#                 """, (user_id, tile_id))
#                 benar_count = cursor.fetchone()['benar']

#                 if benar_count == total_soal:
#                     print(
#                         "[DEBUG] Semua soal benar, status completed dan buka tile berikutnya")
#                     cursor.execute("""
#                         UPDATE user_progress SET status = 'completed'
#                         WHERE user_id = %s AND tile_id = %s
#                     """, (user_id, tile_id))

#                     # Tambah pencapaian jika tile_id istimewa
#                     if tile_id in (15, 31, 47, 63):
#                         print(
#                             "[DEBUG] Menyimpan pencapaian karena semua benar dan tile termasuk spesial")
#                         cursor.execute("""
#                             INSERT INTO user_achievement (user_id, tile_id, achievement_name)
#                             VALUES (%s, %s, %s)
#                         """, (user_id, tile_id, f"Achievement untuk tile {tile_id}"))

#                     # buka tile berikutnya
#                     cursor.execute(
#                         "SELECT position, level_id FROM tiles WHERE id = %s", (tile_id,))
#                     tile_info = cursor.fetchone()
#                     current_position = tile_info['position']
#                     level_id = tile_info['level_id']

#                     cursor.execute("SELECT id FROM tiles WHERE level_id = %s AND position = %s",
#                                    (level_id, current_position + 1))
#                     next_tile = cursor.fetchone()

#                     if next_tile:
#                         print(
#                             f"[DEBUG] Membuka tile selanjutnya: {next_tile['id']}")
#                         cursor.execute("""
#                             INSERT INTO user_progress (user_id, tile_id, status, lives)
#                             VALUES (%s, %s, %s, %s)
#                             ON DUPLICATE KEY UPDATE status = 'in_progress'
#                         """, (user_id, next_tile['id'], 'in_progress', 3))
#                 else:
#                     print("[DEBUG] Ada jawaban salah, tidak bisa naik tile")

#         conn.commit()
#         cursor.close()
#         conn.close()

#         return {'correct': benar, 'remaining_lives': lives}


@api.expect(jawaban_model)
@api.route('/jawab')
class Jawab(Resource):
    def post(self):
        data = request.json
        user_id = data.get('user_id')
        tile_id = data.get('tile_id')
        soal_id = data.get('soal_id')
        jawaban = data.get('jawaban')

        print(
            f"[DEBUG] POST jawab - user_id: {user_id}, tile_id: {tile_id}, soal_id: {soal_id}, jawaban: {jawaban}")

        if not all([user_id, tile_id, soal_id, jawaban]):
            print("[DEBUG] Data tidak lengkap")
            return {'message': 'Data tidak lengkap'}, 400

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT jawaban_benar FROM soal WHERE id = %s", (soal_id,))
        soal = cursor.fetchone()
        if not soal:
            print("[DEBUG] Soal tidak ditemukan")
            return {'message': 'Soal tidak ditemukan'}, 404

        jawaban_benar = soal['jawaban_benar']
        benar = jawaban.upper() == jawaban_benar.upper()
        print(f"[DEBUG] Jawaban benar: {jawaban_benar}, User benar: {benar}")

        cursor.execute(
            "SELECT * FROM user_progress WHERE user_id = %s AND tile_id = %s", (user_id, tile_id))
        progress = cursor.fetchone()

        if not progress:
            print("[DEBUG] Membuat progress baru")
            lives = 3
            status = 'in_progress'
            cursor.execute("""
                INSERT INTO user_progress (user_id, tile_id, status, lives)
                VALUES (%s, %s, %s, %s)
            """, (user_id, tile_id, status, lives))
        else:
            lives = progress['lives']
            status = progress['status']
            print(
                f"[DEBUG] Progress ditemukan - lives: {lives}, status: {status}")
            if status in ('completed', 'failed'):
                return {'correct': True, 'remaining_lives': lives}

        cursor.execute("""
            SELECT * FROM jawaban_user
            WHERE user_id = %s AND tile_id = %s AND soal_id = %s
        """, (user_id, tile_id, soal_id))
        existing = cursor.fetchone()
        if existing:
            print("[DEBUG] Jawaban sudah pernah dikirim")
            return {'correct': existing['benar'], 'remaining_lives': lives}
        if benar:
            cursor.execute("""
                INSERT INTO jawaban_user (user_id, tile_id, soal_id, jawaban, benar)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, tile_id, soal_id, jawaban.upper(), benar))
        else:
            lives = max(0, lives - 1)
            print(f"[DEBUG] Jawaban salah, lives berkurang jadi: {lives}")
            cursor.execute("UPDATE user_progress SET lives = %s WHERE user_id = %s AND tile_id = %s",
                           (lives, user_id, tile_id))

        # cursor.execute("""
        #     INSERT INTO jawaban_user (user_id, tile_id, soal_id, jawaban, benar)
        #     VALUES (%s, %s, %s, %s, %s)
        # """, (user_id, tile_id, soal_id, jawaban.upper(), benar))

        # if not benar:
        #     lives = max(0, lives - 1)
        #     print(f"[DEBUG] Jawaban salah, lives berkurang jadi: {lives}")
        #     cursor.execute("UPDATE user_progress SET lives = %s WHERE user_id = %s AND tile_id = %s",
        #                    (lives, user_id, tile_id))

        if lives == 0:
            print("[DEBUG] Lives habis, status gagal")
            cursor.execute("""
                UPDATE user_progress SET status = 'failed'
                WHERE user_id = %s AND tile_id = %s
            """, (user_id, tile_id))
        else:
            cursor.execute("""
                SELECT COUNT(*) AS total FROM soal
                JOIN tiles t ON soal.kumpulan_soal_id = t.kumpulan_soal_id
                WHERE t.id = %s
            """, (tile_id,))
            total_soal = cursor.fetchone()['total']

            cursor.execute("""
                SELECT COUNT(*) AS answered FROM jawaban_user
                WHERE user_id = %s AND tile_id = %s
            """, (user_id, tile_id))
            answered = cursor.fetchone()['answered']

            print(
                f"[DEBUG] Total soal: {total_soal}, Sudah dijawab: {answered}")

            if answered >= total_soal:
                # Cek apakah semua jawaban benar
                cursor.execute("""
                    SELECT COUNT(*) AS benar FROM jawaban_user
                    WHERE user_id = %s AND tile_id = %s AND benar = 1
                """, (user_id, tile_id))
                benar_count = cursor.fetchone()['benar']

                if benar_count == total_soal:
                    print(
                        "[DEBUG] Semua soal benar, status completed dan buka tile berikutnya")
                    cursor.execute("""
                        UPDATE user_progress SET status = 'completed'
                        WHERE user_id = %s AND tile_id = %s
                    """, (user_id, tile_id))

                    # buka tile berikutnya
                    cursor.execute(
                        "SELECT position, level_id FROM tiles WHERE id = %s", (tile_id,))
                    tile_info = cursor.fetchone()
                    current_position = tile_info['position']
                    level_id = tile_info['level_id']

                    cursor.execute("SELECT id FROM tiles WHERE level_id = %s AND position = %s",
                                   (level_id, current_position + 1))
                    next_tile = cursor.fetchone()

                    if next_tile:
                        print(
                            f"[DEBUG] Membuka tile selanjutnya: {next_tile['id']}")
                        cursor.execute("""
                            INSERT INTO user_progress (user_id, tile_id, status, lives)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE status = 'in_progress'
                        """, (user_id, next_tile['id'], 'in_progress', 3))
                else:
                    print("[DEBUG] Ada jawaban salah, tidak bisa naik tile")

        conn.commit()
        cursor.close()
        conn.close()

        return {'correct': benar, 'remaining_lives': lives}
