import mysql.connector
from datetime import datetime

# ---------------- CONEXIÓN ----------------
def conectar():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",          # Cambia según tu configuración
        password="toor",          # Agrega tu contraseña si es necesaria
        database="biblioteca" # Asegúrate de que tu DB se llame así
    )

# ---------------- LOGS ----------------
def log_evento(mensaje):
    with open("biblioteca.log", "a") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensaje}\n")

# ---------------- FUNCIONES LIBROS ----------------
def registrar_libro():
    titulo = input("Título: ").strip()
    autor = input("Autor: ").strip()
    try:
        anio = int(input("Año: "))
    except ValueError:
        print("❌ Año inválido.")
        return

    if not titulo or not autor:
        print("❌ Todos los campos son obligatorios.")
        return

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO libros (titulo, autor, anio, disponible) VALUES (%s, %s, %s, %s)",
        (titulo, autor, anio, True)
    )
    conexion.commit()
    conexion.close()
    log_evento(f"Libro registrado: {titulo}")
    print("✅ Libro registrado correctamente.")

def listar_libros():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM libros")
    for libro in cursor.fetchall():
        estado = "Disponible" if libro["disponible"] else "Prestado"
        print(f"[{libro['id']}] {libro['titulo']} - {libro['autor']} ({libro['anio']}) - {estado}")
    conexion.close()

def buscar_libro():
    palabra = input("Buscar por título o autor: ").strip()
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM libros WHERE titulo LIKE %s OR autor LIKE %s", (f"%{palabra}%", f"%{palabra}%"))
    resultados = cursor.fetchall()
    if not resultados:
        print("❌ No se encontraron libros.")
    else:
        for libro in resultados:
            estado = "Disponible" if libro["disponible"] else "Prestado"
            print(f"[{libro['id']}] {libro['titulo']} - {libro['autor']} ({libro['anio']}) - {estado}")
    conexion.close()

# ---------------- FUNCIONES USUARIOS ----------------
def registrar_usuario():
    nombre = input("Nombre del usuario: ").strip()
    tipo = input("Tipo (Alumno / Profesor / Otro): ").strip()
    if not nombre or not tipo:
        print("❌ Todos los campos son obligatorios.")
        return
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO usuarios (nombre, tipo) VALUES (%s, %s)", (nombre, tipo))
    conexion.commit()
    conexion.close()
    log_evento(f"Usuario registrado: {nombre}")
    print("✅ Usuario registrado correctamente.")

def listar_usuarios():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios")
    for usuario in cursor.fetchall():
        print(f"[{usuario['id']}] {usuario['nombre']} - {usuario['tipo']}")
    conexion.close()

def buscar_usuario():
    nombre = input("Buscar usuario por nombre: ").strip()
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE nombre LIKE %s", (f"%{nombre}%",))
    resultados = cursor.fetchall()
    if not resultados:
        print("❌ No se encontraron usuarios.")
    else:
        for usuario in resultados:
            print(f"[{usuario['id']}] {usuario['nombre']} - {usuario['tipo']}")
    conexion.close()

# ---------------- FUNCIONES PRÉSTAMOS ----------------
def registrar_prestamo():
    try:
        id_usuario = int(input("ID del usuario: "))
        id_libro = int(input("ID del libro: "))
    except ValueError:
        print("❌ IDs inválidos.")
        return

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    # Verificar existencia de usuario
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id_usuario,))
    usuario = cursor.fetchone()
    if not usuario:
        print("❌ Usuario no encontrado.")
        conexion.close()
        return

    # Verificar disponibilidad del libro
    cursor.execute("SELECT * FROM libros WHERE id = %s", (id_libro,))
    libro = cursor.fetchone()
    if not libro:
        print("❌ Libro no encontrado.")
        conexion.close()
        return
    if not libro["disponible"]:
        print("❌ El libro no está disponible.")
        conexion.close()
        return

    # Registrar préstamo
    fecha = datetime.now().date()
    cursor.execute(
        "INSERT INTO prestamos (id_usuario, id_libro, fecha_prestamo, fecha_devolucion) VALUES (%s, %s, %s, NULL)",
        (id_usuario, id_libro, fecha)
    )
    cursor.execute("UPDATE libros SET disponible = %s WHERE id = %s", (False, id_libro))
    conexion.commit()
    conexion.close()
    log_evento(f"Préstamo registrado: Usuario {id_usuario} - Libro {id_libro}")
    print("✅ Préstamo registrado correctamente.")

def devolver_libro():
    try:
        id_prestamo = int(input("ID del préstamo: "))
    except ValueError:
        print("❌ ID inválido.")
        return

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT * FROM prestamos WHERE id = %s", (id_prestamo,))
    prestamo = cursor.fetchone()
    if not prestamo:
        print("❌ Préstamo no encontrado.")
        conexion.close()
        return
    if prestamo["fecha_devolucion"]:
        print("❌ El libro ya fue devuelto.")
        conexion.close()
        return

    # Marcar devolución
    fecha_dev = datetime.now().date()
    cursor.execute("UPDATE prestamos SET fecha_devolucion = %s WHERE id = %s", (fecha_dev, id_prestamo))
    cursor.execute("UPDATE libros SET disponible = %s WHERE id = %s", (True, prestamo["id_libro"]))
    conexion.commit()
    conexion.close()
    log_evento(f"Devolución registrada: Préstamo {id_prestamo}")
    print("✅ Libro devuelto correctamente.")

def prestamos_activos():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.id, u.nombre, l.titulo, p.fecha_prestamo 
        FROM prestamos p 
        JOIN usuarios u ON p.id_usuario = u.id 
        JOIN libros l ON p.id_libro = l.id 
        WHERE p.fecha_devolucion IS NULL
    """)
    prestamos = cursor.fetchall()
    if not prestamos:
        print("No hay préstamos activos.")
    else:
        for p in prestamos:
            print(f"[{p['id']}] {p['nombre']} - {p['titulo']} (Prestado el {p['fecha_prestamo']})")
    conexion.close()

# ---------------- MENÚS ----------------
def menu_libros():
    while True:
        print("\n--- MENÚ LIBROS ---")
        print("1. Registrar libro")
        print("2. Listar libros")
        print("3. Buscar libro")
        print("4. Volver al menú principal")
        opcion = input("Selecciona una opción: ")
        if opcion == "1": registrar_libro()
        elif opcion == "2": listar_libros()
        elif opcion == "3": buscar_libro()
        elif opcion == "4": break
        else: print("❌ Opción inválida.")

def menu_usuarios():
    while True:
        print("\n--- MENÚ USUARIOS ---")
        print("1. Registrar usuario")
        print("2. Listar usuarios")
        print("3. Buscar usuario")
        print("4. Volver al menú principal")
        opcion = input("Selecciona una opción: ")
        if opcion == "1": registrar_usuario()
        elif opcion == "2": listar_usuarios()
        elif opcion == "3": buscar_usuario()
        elif opcion == "4": break
        else: print("❌ Opción inválida.")

def menu_prestamos():
    while True:
        print("\n--- MENÚ PRÉSTAMOS ---")
        print("1. Registrar préstamo")
        print("2. Devolver libro")
        print("3. Ver préstamos activos")
        print("4. Volver al menú principal")
        opcion = input("Selecciona una opción: ")
        if opcion == "1": registrar_prestamo()
        elif opcion == "2": devolver_libro()
        elif opcion == "3": prestamos_activos()
        elif opcion == "4": break
        else: print("❌ Opción inválida.")

# ---------------- MENÚ PRINCIPAL ----------------
def menu_principal():
    while True:
        print("\n===== SISTEMA DE BIBLIOTECA =====")
        print("1. Libros")
        print("2. Usuarios")
        print("3. Préstamos")
        print("4. Salir")

        opcion = input("Selecciona una opción: ")
        if opcion == "1": menu_libros()
        elif opcion == "2": menu_usuarios()
        elif opcion == "3": menu_prestamos()
        elif opcion == "4":
            print("👋 Saliendo del sistema...")
            break
        else:
            print("❌ Opción inválida.")

# ---------------- EJECUCIÓN ----------------
if __name__ == "__main__":
    menu_principal()
