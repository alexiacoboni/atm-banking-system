from flask import Flask, request, jsonify, render_template
import mysql.connector
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="banca"
    )

@app.route('/')
def home():
    print("Folderul curent este:", os.getcwd())
    print("Există index.html?:", os.path.exists('templates/index.html'))
    return render_template('index.html')

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "Server ok"}), 200

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "Date JSON lipsă"}), 400

        username = data.get('username', '').lower()
        parola = data.get('password', '')

        if not username or not parola:
            return jsonify({"success": False, "message": "Username și parola sunt necesare"}), 400

        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM conturi WHERE nume = %s AND parola = %s", (username, parola))
        user = cursor.fetchone()

        if user:
            return jsonify({"success": True, "rol": user["rol"]})
        else:
            return jsonify({"success": False, "message": "Date incorecte"}), 401

    except mysql.connector.Error as err:
        print("Eroare DB:", err)
        return jsonify({"success": False, "message": "Eroare server"}), 500

    except Exception as e:
        import traceback
        print("EROARE NEAȘTEPTATĂ:", e)
        traceback.print_exc()
        return jsonify({"success": False, "message": "Eroare server"}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ===================== CLIENT =====================

@app.route('/client/verificare_sold', methods=['POST'])
def verificare_sold():
    data = request.json
    utilizator = data.get('utilizator')
    if not utilizator:
        return jsonify({"message": "Utilizatorul este necesar"}), 400
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT sold FROM conturi WHERE nume = %s", (utilizator,))
    sold = cursor.fetchone()
    cursor.close()
    conn.close()
    if sold is not None:
        return jsonify({"sold": sold[0]})
    else:
        return jsonify({"message": "Utilizator inexistent"}), 404


from datetime import datetime

@app.route('/client/retragere_bani', methods=['POST'])
def retragere_bani():
    data = request.json
    utilizator = data.get('utilizator')
    suma = data.get('suma')

    if not utilizator or suma is None:
        return jsonify({"message": "Utilizator și suma sunt necesare"}), 400

    try:
        suma = float(suma)
    except:
        return jsonify({"message": "Suma trebuie să fie un număr"}), 400

    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT sold FROM conturi WHERE nume = %s", (utilizator,))
        sold = cursor.fetchone()
        if not sold:
            return jsonify({"message": "Utilizator inexistent"}), 404
        if suma > sold['sold']:
            return jsonify({"message": "Fonduri insuficiente."}), 400

        cursor.execute("UPDATE conturi SET sold = sold - %s WHERE nume = %s", (suma, utilizator))

        # Salvează tranzacția în istoric
        cursor.execute("""
            INSERT INTO tranzactii (username, tip, suma)
            VALUES (%s, 'retragere', %s)
        """, (utilizator, suma))

        cursor.execute("SELECT sold FROM conturi WHERE nume = %s", (utilizator,))
        sold_actualizat = cursor.fetchone()

        conn.commit()

        mesaj = f"Retragere reușită. Sold actualizat: {sold_actualizat['sold']:.2f} RON"
        return jsonify({"message": mesaj, "sold": sold_actualizat['sold']})

    except Exception as e:
        conn.rollback()
        print("Eroare:", e)
        return jsonify({"message": "Eroare la retragere."}), 500

    finally:
        cursor.close()
        conn.close()


@app.route('/client/depunere_bani', methods=['POST'])
def depunere_bani():
    data = request.json
    utilizator = data.get('utilizator')
    suma = data.get('suma')
    if not utilizator or suma is None:
        return jsonify({"message": "Utilizator și suma sunt necesare"}), 400
    try:
        suma = float(suma)
    except:
        return jsonify({"message": "Suma trebuie să fie un număr"}), 400

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE conturi SET sold = sold + %s WHERE nume = %s", (suma, utilizator))

    # Salvează tranzacția în istoric
    cursor.execute("""
        INSERT INTO tranzactii (username, tip, suma)
        VALUES (%s, 'depunere', %s)
    """, (utilizator, suma))

    conn.commit()

    cursor.execute("SELECT sold FROM conturi WHERE nume = %s", (utilizator,))
    sold_actualizat = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({"message": "Depunere efectuată cu succes.", "sold": sold_actualizat[0]})

@app.route('/client/transfer_bani', methods=['POST'])
def transfer_bani():
    data = request.json
    utilizator = data.get('utilizator')
    destinatar = data.get('destinatar')
    suma = data.get('suma')
    if not utilizator or not destinatar or suma is None:
        return jsonify({"message": "Utilizator, destinatar și suma sunt necesare"}), 400
    try:
        suma = float(suma)
    except:
        return jsonify({"message": "Suma trebuie să fie un număr"}), 400

    utilizator = utilizator.strip().lower()
    destinatar = destinatar.strip().lower()

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT sold FROM conturi WHERE LOWER(nume) = %s", (utilizator,))
    sold = cursor.fetchone()

    cursor.execute("SELECT nume FROM conturi WHERE LOWER(nume) = %s", (destinatar,))
    destinatar_exista = cursor.fetchone()

    if sold and destinatar_exista and suma <= sold[0]:
        cursor.execute("UPDATE conturi SET sold = sold - %s WHERE LOWER(nume) = %s", (suma, utilizator))
        cursor.execute("UPDATE conturi SET sold = sold + %s WHERE LOWER(nume) = %s", (suma, destinatar))

        # Salvează tranzacția în istoric
        cursor.execute("""
            INSERT INTO tranzactii (username, tip, suma, cont_destinatar)
            VALUES (%s, 'transfer', %s, %s)
        """, (utilizator, suma, destinatar))

        conn.commit()

        cursor.execute("SELECT sold FROM conturi WHERE LOWER(nume) = %s", (utilizator,))
        sold_actualizat = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({"message": "Transfer realizat cu succes.", "sold": sold_actualizat[0]})
    else:
        cursor.close()
        conn.close()
        return jsonify({"message": "Transfer eșuat. Cont inexistent sau fonduri insuficiente."}), 400

@app.route('/client/verifica_destinatar/<nume>', methods=['GET'])
def verifica_destinatar(nume):
    nume = nume.strip().lower()
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM conturi WHERE LOWER(nume) = %s", (nume,))
    exista = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return jsonify({"exista": exista})

@app.route('/client/istoric_tranzactii/<utilizator>', methods=['GET'])
def istoric_tranzactii(utilizator):
    if not utilizator:
        return jsonify({"message": "Utilizatorul este necesar"}), 400

    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT tip, suma, cont_destinatar, DATE_FORMAT(data, '%%Y-%%m-%%d %%H:%%i') as data
        FROM tranzactii
        WHERE username = %s
        ORDER BY data DESC
        LIMIT 20
    """, (utilizator,))
    tranzactii_raw = cursor.fetchall()
    cursor.close()
    conn.close()

    tranzactii_formatate = []
    for tr in tranzactii_raw:
        if tr['tip'] == 'transfer':
            mesaj = f"[{tr['data']}] Transfer către {tr['cont_destinatar']}: {tr['suma']} RON"
        else:
            mesaj = f"[{tr['data']}] {tr['tip'].capitalize()}: {tr['suma']} RON"
        tranzactii_formatate.append(mesaj)

    return jsonify({"tranzactii": tranzactii_formatate})







# ===================== ADMIN =====================

@app.route('/admin/creare_cont', methods=['POST'])
def creare_cont():
    data = request.json
    nume = data.get('nume')
    parola = data.get('parola')
    tip = data.get('tip')
    rol = data.get('rol')
    sold_initial = data.get('sold_initial', 0)
    if not all([nume, parola, tip, rol]):
        return jsonify({"message": "Toate câmpurile sunt obligatorii"}), 400
    try:
        sold_initial = float(sold_initial)
    except:
        return jsonify({"message": "Soldul inițial trebuie să fie un număr valid"}), 400
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conturi (nume, parola, tip, rol, sold) VALUES (%s, %s, %s, %s, %s)",
                   (nume, parola, tip, rol, sold_initial))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Cont creat cu succes"})

@app.route('/admin/inchidere_cont', methods=['POST'])
def inchidere_cont():
    data = request.json
    nume = data.get('username')
    if not nume:
        return jsonify({"message": "Numele contului este necesar"}), 400
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conturi WHERE nume = %s", (nume,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": f"Contul {nume} a fost șters cu succes"})

@app.route('/admin/listare_conturi')
def listare_conturi():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nume, tip, rol, sold FROM conturi")
    conturi = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"conturi": conturi})

@app.route('/admin/conturi_curente')
def conturi_curente():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nume, sold FROM conturi WHERE tip = 'curent'")
    conturi = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"conturi_curente": conturi})

@app.route('/admin/depozite_bancare')
def depozite_bancare():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nume, sold FROM conturi WHERE tip = 'deposit'")
    depozite = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"depozite_bancare": depozite})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
