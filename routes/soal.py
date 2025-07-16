from flask import request
from flask_restx import Namespace, Resource, fields
from db import get_connection
import random

api = Namespace(
    'Soal', description='Soal berdasarkan Tile dan Jawaban Pengguna')

# ==== Konstanta ====
host_url = "https://nngwj5fn-5006.asse.devtunnels.ms"
page_size = 2
auto_finish_tiles = [16, 32, 48, 64]
gambar_mapping = {
    16: "hijau.png",
    32: "pink.png",
    48: "orange.png",
    64: "biru.png"
}


# ==== Schema ====
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
    'soal': fields.List(fields.Nested(soal_model)),
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


# ==== Utils ====
def fisher_yates_shuffle(arr):
    n = len(arr)
    for i in range(n - 1, 0, -1):
        j = random.randint(0, i)
        arr[i], arr[j] = arr[j], arr[i]
    return arr


def get_kumpulan_soal_range_from_tile(tile_id):
    if 1 <= tile_id <= 15:
        return range(1, 31)
    elif 17 <= tile_id <= 32:
        return range(31, 61)
    elif 33 <= tile_id <= 48:
        return range(61, 91)
    elif 49 <= tile_id <= 64:
        return range(91, 121)
    return None


# ==== Endpoint GET Soal ====
@api.route('/<int:tile_id>')
class SoalByTile(Resource):
    @api.doc(params={'user_id': 'ID pengguna', 'page': 'Soal keberapa'})
    @api.marshal_with(response_model)
    def get(self, tile_id):
        user_id = request.args.get('user_id', type=int)
        page = request.args.get('page', default=1, type=int)

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if tile_id in auto_finish_tiles:
            gambar = gambar_mapping.get(tile_id, "default.jpg")
            cursor.execute("""
                INSERT INTO user_achievement (user_id, tile_id, achievement_name, gambar)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    achievement_name = VALUES(achievement_name),
                    gambar = VALUES(gambar)
            """, (user_id, tile_id, f"Achievement Langsung untuk tile {tile_id}", gambar))

            cursor.execute("""
                INSERT INTO user_progress (user_id, tile_id, status, lives)
                VALUES (%s, %s, 'finished', 3)
                ON DUPLICATE KEY UPDATE status = 'completed'
            """, (user_id, tile_id))

            if tile_id != 64:
                next_tile = tile_id + 1
                cursor.execute("""
                    INSERT INTO user_progress (user_id, tile_id, status, lives)
                    VALUES (%s, %s, 'unlocked', 3)
                    ON DUPLICATE KEY UPDATE status = IF(status='locked', 'unlocked', status)
                """, (user_id, next_tile))

            conn.commit()
            cursor.close()
            conn.close()
            return {
                'soal': [],
                'page': 1,
                'total_soal': 0,
                'lives': 3,
                'status': 'auto_finished'
            }

        # === Proses normal soal ===
        kumpulan_range = get_kumpulan_soal_range_from_tile(tile_id)
        if not kumpulan_range:
            return {'soal': [], 'page': page, 'total_soal': 0, 'lives': 0, 'status': 'invalid'}, 404

        min_id, max_id = min(kumpulan_range), max(kumpulan_range)

        cursor.execute("""
            SELECT id FROM soal
            WHERE kumpulan_soal_id BETWEEN %s AND %s
        """, (min_id, max_id))
        all_soal_ids = [row['id'] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT soal_id FROM soal_shuffle_user
            WHERE user_id = %s AND tile_id = %s
            ORDER BY urutan
        """, (user_id, tile_id))
        displayed = [row['soal_id'] for row in cursor.fetchall()]

        remaining = [sid for sid in all_soal_ids if sid not in displayed]
        shuffled = fisher_yates_shuffle(remaining)[:page_size]

        for idx, sid in enumerate(shuffled, start=len(displayed) + 1):
            cursor.execute("""
                INSERT INTO soal_shuffle_user (user_id, tile_id, soal_id, urutan)
                VALUES (%s, %s, %s, %s)
            """, (user_id, tile_id, sid, idx))
        conn.commit()

        displayed += shuffled
        start = (page - 1) * page_size
        end = start + page_size
        ids_to_fetch = displayed[start:end]

        # Cetak jawaban benar
        cursor.execute(f"""
            SELECT id, pertanyaan, jawaban_benar FROM soal
            WHERE id IN ({','.join(['%s'] * len(ids_to_fetch))})
        """, ids_to_fetch)
        for row in cursor.fetchall():
            print(
                f"  - Soal ID {row['id']}: {row['jawaban_benar']} | {row['pertanyaan'][:50]}...")

        # Ambil data soal
        soals = []
        for sid in ids_to_fetch:
            cursor.execute("SELECT * FROM soal WHERE id = %s", (sid,))
            soal = cursor.fetchone()
            if soal:
                soal['gambar_url'] = f"{host_url}/static/uploads/{soal['gambar']}" if soal.get(
                    'gambar') else ''
                for opt in ['a', 'b', 'c', 'd']:
                    key = f'gambar_{opt}'
                    soal[f'gambar_{opt}_url'] = f"{host_url}/static/uploads/{soal[key]}" if soal.get(
                        key) else ''
                soals.append(soal)

        # Ambil nyawa user
        cursor.execute(
            "SELECT lives FROM user_progress WHERE user_id = %s AND tile_id = %s", (user_id, tile_id))
        row = cursor.fetchone()
        lives = row['lives'] if row else 3

        total_soal = len(displayed)
        status = 'finished' if end >= total_soal else 'in_progress'

        cursor.close()
        conn.close()
        return {
            'soal': soals,
            'page': page,
            'total_soal': total_soal,
            'lives': lives,
            'status': status
        }


# ==== Endpoint POST Jawaban ====
@api.expect(jawaban_model)
@api.route('/jawab')
class Jawab(Resource):
    def post(self):
        data = request.json
        user_id = data.get('user_id')
        tile_id = data.get('tile_id')
        soal_id = data.get('soal_id')
        jawaban = data.get('jawaban', '').upper()

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT jawaban_benar FROM soal WHERE id = %s", (soal_id,))
        soal = cursor.fetchone()
        if not soal:
            return {'message': 'Soal tidak ditemukan'}, 404

        benar = jawaban == soal['jawaban_benar'].upper()

        cursor.execute(
            "SELECT * FROM user_progress WHERE user_id = %s AND tile_id = %s", (user_id, tile_id))
        progress = cursor.fetchone()
        lives = progress['lives'] if progress else 3

        if not progress:
            cursor.execute("INSERT INTO user_progress (user_id, tile_id, lives, status) VALUES (%s, %s, %s, 'in_progress')",
                           (user_id, tile_id, lives))
        elif progress['status'] in ('completed', 'failed'):
            return {'correct': benar, 'remaining_lives': lives}

        cursor.execute("""
            SELECT * FROM jawaban_user
            WHERE user_id = %s AND tile_id = %s AND soal_id = %s
        """, (user_id, tile_id, soal_id))
        if cursor.fetchone():
            return {'correct': benar, 'remaining_lives': lives}

        if benar:
            cursor.execute("""
                INSERT INTO jawaban_user (user_id, tile_id, soal_id, jawaban, benar)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, tile_id, soal_id, jawaban, True))
        else:
            lives = max(0, lives - 1)
            cursor.execute("""
                UPDATE user_progress SET lives = %s WHERE user_id = %s AND tile_id = %s
            """, (lives, user_id, tile_id))

        cursor.execute("""
            SELECT COUNT(*) AS answered FROM jawaban_user
            WHERE user_id = %s AND tile_id = %s
        """, (user_id, tile_id))
        answered = cursor.fetchone()['answered']

        if answered >= 2:
            cursor.execute("""
                SELECT COUNT(*) AS benar FROM jawaban_user
                WHERE user_id = %s AND tile_id = %s AND benar = 1
            """, (user_id, tile_id))
            benar_count = cursor.fetchone()['benar']

            if benar_count >= 2:
                cursor.execute("""
                    UPDATE user_progress SET status = 'completed'
                    WHERE user_id = %s AND tile_id = %s
                """, (user_id, tile_id))

                cursor.execute(
                    "SELECT position, level_id FROM tiles WHERE id = %s", (tile_id,))
                info = cursor.fetchone()
                next_pos = info['position'] + 1
                level_id = info['level_id']

                cursor.execute(
                    "SELECT id FROM tiles WHERE level_id = %s AND position = %s", (level_id, next_pos))
                next_tile = cursor.fetchone()
                if next_tile:
                    cursor.execute("""
                        INSERT INTO user_progress (user_id, tile_id, lives, status)
                        VALUES (%s, %s, %s, 'unlocked')
                        ON DUPLICATE KEY UPDATE status = 'unlocked'
                    """, (user_id, next_tile['id'], 3))

        if lives == 0:
            cursor.execute("""
                UPDATE user_progress SET status = 'failed'
                WHERE user_id = %s AND tile_id = %s
            """, (user_id, tile_id))

        conn.commit()
        cursor.close()
        conn.close()
        return {'correct': benar, 'remaining_lives': lives}
