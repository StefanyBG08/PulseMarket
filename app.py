import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

app = Flask(__name__)

# Función para conectarse a la base de datos usando el .env
def conectar_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "pulsemarket"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )

# Crea las tablas automáticamente en PostgreSQL si no existen
def inicializar_db():
    try:
        with conectar_db() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS productos (
                        id SERIAL PRIMARY KEY,
                        nombre VARCHAR(100) NOT NULL,
                        categoria VARCHAR(50) NOT NULL,
                        precio NUMERIC(10, 2) NOT NULL,
                        stock INT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS pedidos (
                        id VARCHAR(20) PRIMARY KEY,
                        cliente VARCHAR(100) NOT NULL,
                        producto VARCHAR(100) NOT NULL,
                        total NUMERIC(10, 2) NOT NULL,
                        estado VARCHAR(30) NOT NULL
                    );
                """)
                conexion.commit()
                print("Base de datos e historial de tablas listos.")
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")

# Rutas de la app
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/api/stats")
def estadisticas():
    try:
        with conectar_db() as conexion:
            with conexion.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT COUNT(*) AS total_prod FROM productos;")
                prod = cursor.fetchone()
                cursor.execute("SELECT COUNT(*) AS total_ped, COALESCE(SUM(total), 0) AS total_ventas FROM pedidos;")
                ped = cursor.fetchone()
                
                return jsonify({
                    "ventas_totales": float(ped["total_ventas"]),
                    "total_pedidos": ped["total_ped"],
                    "total_productos": prod["total_prod"],
                    "pedidos_completados": 0,
                    "ventas_mensuales": [0] * 12
                })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/productos", methods=["GET", "POST"])
def manejar_productos():
    with conectar_db() as conexion:
        with conexion.cursor(cursor_factory=RealDictCursor) as cursor:
            if request.method == "POST":
                data = request.json
                cursor.execute(
                    "INSERT INTO productos (nombre, categoria, precio, stock) VALUES (%s, %s, %s, %s) RETURNING *;",
                    (data["nombre"], data["categoria"], data["precio"], data["stock"])
                )
                conexion.commit()
                return jsonify(cursor.fetchone()), 201
            else:
                cursor.execute("SELECT * FROM productos ORDER BY id ASC;")
                return jsonify(cursor.fetchall())

@app.route("/api/pedidos")
def obtener_pedidos():
    with conectar_db() as conexion:
        with conexion.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM pedidos ORDER BY id DESC;")
            return jsonify(cursor.fetchall())

if __name__ == "__main__":
    inicializar_db()
    app.run(host="0.0.0.0", port=5000, debug=True)