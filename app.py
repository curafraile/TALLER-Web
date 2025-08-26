import os
import sqlite3
import psycopg2
from flask import Flask, render_template, request, redirect, session, send_file, g
from docx import Document
from io import BytesIO
from datetime import date, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-super-secret-key-here")

# ================== Database Connection ==================
def get_db():
    if 'db' not in g:
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if DATABASE_URL:
            # Conexión a PostgreSQL (producción)
            try:
                g.db = psycopg2.connect(DATABASE_URL)
                g.db_type = 'postgresql'
            except Exception as e:
                print(f"Error PostgreSQL: {e}, usando SQLite de fallback.")
                g.db = sqlite3.connect('database.db')
                g.db_type = 'sqlite'
                g.db.execute('PRAGMA foreign_keys = ON')
        else:
            # Conexión local SQLite
            g.db = sqlite3.connect('database.db')
            g.db_type = 'sqlite'
            g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db:
        db.close()

# ================== Inicialización ==================
def init_db():
    conn = get_db()
    cur = conn.cursor()

    if g.db_type == 'sqlite':
        cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            nombre TEXT,
            apellido TEXT,
            rol TEXT,
            clave TEXT,
            perfil TEXT
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            año INTEGER
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS alumnos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            apellido TEXT,
            curso_id INTEGER,
            FOREIGN KEY(curso_id) REFERENCES cursos(id)
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS docente_cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            docente_id INTEGER,
            curso_id INTEGER,
            FOREIGN KEY(docente_id) REFERENCES usuarios(id),
            FOREIGN KEY(curso_id) REFERENCES cursos(id)
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alumno_id INTEGER,
            docente_id INTEGER,
            curso_id INTEGER,
            nota REAL,
            fecha TEXT,
            FOREIGN KEY(alumno_id) REFERENCES alumnos(id)
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS asistencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alumno_id INTEGER,
            docente_id INTEGER,
            curso_id INTEGER,
            fecha TEXT,
            presente INTEGER,
            FOREIGN KEY(alumno_id) REFERENCES alumnos(id)
        )""")
        cur.execute("SELECT * FROM usuarios WHERE rol='admin'")
        if not cur.fetchone():
            cur.execute("INSERT INTO usuarios (usuario, nombre, apellido, rol, clave, perfil) VALUES (?,?,?,?,?,?)",
                        ("admin", "Admin", "Taller", "admin", "1234", ""))
    else:  # PostgreSQL
        cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            usuario TEXT UNIQUE,
            nombre TEXT,
            apellido TEXT,
            rol TEXT,
            clave TEXT,
            perfil TEXT
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS cursos (
            id SERIAL PRIMARY KEY,
            nombre TEXT,
            año INTEGER
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS alumnos (
            id SERIAL PRIMARY KEY,
            nombre TEXT,
            apellido TEXT,
            curso_id INTEGER REFERENCES cursos(id)
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS docente_cursos (
            id SERIAL PRIMARY KEY,
            docente_id INTEGER REFERENCES usuarios(id),
            curso_id INTEGER REFERENCES cursos(id)
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS notas (
            id SERIAL PRIMARY KEY,
            alumno_id INTEGER REFERENCES alumnos(id),
            docente_id INTEGER REFERENCES usuarios(id),
            curso_id INTEGER REFERENCES cursos(id),
            nota REAL,
            fecha TEXT
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS asistencia (
            id SERIAL PRIMARY KEY,
            alumno_id INTEGER REFERENCES alumnos(id),
            docente_id INTEGER REFERENCES usuarios(id),
            curso_id INTEGER REFERENCES cursos(id),
            fecha TEXT,
            presente INTEGER
        )""")
        cur.execute("SELECT * FROM usuarios WHERE rol='admin'")
        if not cur.fetchone():
            cur.execute("INSERT INTO usuarios (usuario, nombre, apellido, rol, clave, perfil) VALUES (%s,%s,%s,%s,%s,%s)",
                        ("admin", "Admin", "Taller", "admin", "1234", ""))

    conn.commit()
    cur.close()

with app.app_context():
    init_db()

# ================== Login ==================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario_form = request.form["usuario"]
        clave = request.form["clave"]
        conn = get_db()
        cur = conn.cursor()
        if g.db_type == 'sqlite':
            cur.execute("SELECT * FROM usuarios WHERE usuario=? AND clave=?", (usuario_form, clave))
        else:
            cur.execute("SELECT * FROM usuarios WHERE usuario=%s AND clave=%s", (usuario_form, clave))
        usuario = cur.fetchone()
        cur.close()
        if usuario:
            session["usuario_id"] = usuario[0]
            session["rol"] = usuario[4]
            return redirect("/admin" if usuario[4]=="admin" else "/docente")
        else:
            return "Usuario o clave incorrecta"
    return render_template("login.html")

# ================== Control de exportaciones ==================
def check_admin():
    return "rol" in session and session["rol"] == "admin"

def check_docente():
    return "rol" in session and session["rol"] == "docente"

# ================== Exportar Notas ==================
@app.route("/exportar_notas/<int:curso_id>")
def exportar_notas(curso_id):
    if not check_admin():
        return redirect("/")
    # --- resto del código igual que tu versión original ---
    # (Document, tabla, fetch de notas y send_file)
    ...

# ================== Exportar Asistencia ==================
@app.route("/exportar_asistencia/<int:curso_id>")
def exportar_asistencia(curso_id):
    if not check_admin():
        return redirect("/")
    # --- resto igual ---
    ...

# ================== Docente ==================
@app.route("/docente")
def docente():
    if not check_docente():
        return redirect("/")
    docente_id = session["usuario_id"]
    conn = get_db()
    cur = conn.cursor()
    if g.db_type=='sqlite':
        cur.execute("SELECT dc.id, c.nombre, c.año, c.id FROM docente_cursos dc JOIN cursos c ON c.id=dc.curso_id WHERE dc.docente_id=?",(docente_id,))
    else:
        cur.execute("SELECT dc.id, c.nombre, c.año, c.id FROM docente_cursos dc JOIN cursos c ON c.id=dc.curso_id WHERE dc.docente_id=%s",(docente_id,))
    asignaciones_raw = cur.fetchall()
    cur.close()
    asignaciones = [(r[3], r[1], r[2]) for r in asignaciones_raw]
    hoy = date.today().isoformat()
    return render_template("docente.html", asignaciones=asignaciones, today=hoy)

# ================== Cerrar sesión ==================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
