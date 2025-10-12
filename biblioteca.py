import mysql.connector
from datetime import datetime

# ============================================================
# CLASE CONEXIÓN A BASE DE DATOS
# ============================================================
class ConexionBD:
    def __init__(self):
        try:
            self.conn = mysql.connector.connect(
                host="127.0.0.1",
                user="root",       # Cambia según tu configuración
                password="toor",   # Agrega tu contraseña si es necesaria
                database="biblioteca"
            )
            self.cursor = self.conn.cursor(dictionary=True)
        except mysql.connector.Error as e:
            print(f"❌ Error de conexión: {e}")
            self.conn = None
            self.cursor = None

    def ejecutar(self, query, params=None):
        if self.cursor:
            self.cursor.execute(query, params or ())

    def obtener_todos(self):
        return self.cursor.fetchall()

    def obtener_uno(self):
        return self.cursor.fetchone()

    def confirmar(self):
        self.conn.commit()

    def cerrar(self):
        if self.conn:
            self.conn.close()

# ============================================================
# FUNCIÓN DE LOGS
# ============================================================
def log_evento(mensaje):
    with open("biblioteca.log", "a") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensaje}\n")

# ============================================================
# CLASE LIBRO
# ============================================================
class Libro:
    def __init__(self, titulo=None, autor=None, anio=None, disponible=True):
        self.__titulo = titulo
        self.__autor = autor
        self.__anio = anio
        self.__disponible = disponible

    # Getters y setters
    def get_titulo(self): return self.__titulo
    def set_titulo(self, titulo): self.__titulo = titulo

    def get_autor(self): return self.__autor
    def set_autor(self, autor): self.__autor = autor

    def get_anio(self): return self.__anio
    def set_anio(self, anio): self.__anio = anio

    def get_disponible(self): return self.__disponible
    def set_disponible(self, disponible): self.__disponible = disponible

    # Métodos de base de datos
    @staticmethod
    def registrar():
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

        db = ConexionBD()
        db.ejecutar(
            "INSERT INTO libros (titulo, autor, anio, disponible) VALUES (%s, %s, %s, %s)",
            (titulo, autor, anio, True)
        )
        db.confirmar()
        db.cerrar()
        log_evento(f"Libro registrado: {titulo}")
        print("✅ Libro registrado correctamente.")

    @staticmethod
    def listar():
        db = ConexionBD()
        db.ejecutar("SELECT * FROM libros")
        libros = db.obtener_todos()
        for libro in libros:
            estado = "Disponible" if libro["disponible"] else "Prestado"
            print(f"[{libro['id']}] {libro['titulo']} - {libro['autor']} ({libro['anio']}) - {estado}")
        db.cerrar()

    @staticmethod
    def buscar():
        palabra = input("Buscar por título o autor: ").strip()
        db = ConexionBD()
        db.ejecutar("SELECT * FROM libros WHERE titulo LIKE %s OR autor LIKE %s", (f"%{palabra}%", f"%{palabra}%"))
        resultados = db.obtener_todos()
        if not resultados:
            print("❌ No se encontraron libros.")
        else:
            for libro in resultados:
                estado = "Disponible" if libro["disponible"] else "Prestado"
                print(f"[{libro['id']}] {libro['titulo']} - {libro['autor']} ({libro['anio']}) - {estado}")
        db.cerrar()

# ============================================================
# CLASE USUARIO
# ============================================================
class Usuario:
    def __init__(self, nombre=None, tipo=None):
        self.__nombre = nombre
        self.__tipo = tipo

    def get_nombre(self): return self.__nombre
    def set_nombre(self, nombre): self.__nombre = nombre

    def get_tipo(self): return self.__tipo
    def set_tipo(self, tipo): self.__tipo = tipo

    @staticmethod
    def registrar():
        nombre = input("Nombre del usuario: ").strip()
        tipo = input("Tipo (Alumno / Profesor / Otro): ").strip()
        if not nombre or not tipo:
            print("❌ Todos los campos son obligatorios.")
            return

        db = ConexionBD()
        db.ejecutar("INSERT INTO usuarios (nombre, tipo) VALUES (%s, %s)", (nombre, tipo))
        db.confirmar()
        db.cerrar()
        log_evento(f"Usuario registrado: {nombre}")
        print("✅ Usuario registrado correctamente.")

    @staticmethod
    def listar():
        db = ConexionBD()
        db.ejecutar("SELECT * FROM usuarios")
        usuarios = db.obtener_todos()
        for usuario in usuarios:
            print(f"[{usuario['id']}] {usuario['nombre']} - {usuario['tipo']}")
        db.cerrar()

    @staticmethod
    def buscar():
        nombre = input("Buscar usuario por nombre: ").strip()
        db = ConexionBD()
        db.ejecutar("SELECT * FROM usuarios WHERE nombre LIKE %s", (f"%{nombre}%",))
        resultados = db.obtener_todos()
        if not resultados:
            print("❌ No se encontraron usuarios.")
        else:
            for usuario in resultados:
                print(f"[{usuario['id']}] {usuario['nombre']} - {usuario['tipo']}")
        db.cerrar()

# ============================================================
# CLASE PRESTAMO
# ============================================================
class Prestamo:
    @staticmethod
    def registrar():
        try:
            id_usuario = int(input("ID del usuario: "))
            id_libro = int(input("ID del libro: "))
        except ValueError:
            print("❌ IDs inválidos.")
            return

        db = ConexionBD()

        # Verificar usuario
        db.ejecutar("SELECT * FROM usuarios WHERE id = %s", (id_usuario,))
        usuario = db.obtener_uno()
        if not usuario:
            print("❌ Usuario no encontrado.")
            db.cerrar()
            return

        # Verificar libro
        db.ejecutar("SELECT * FROM libros WHERE id = %s", (id_libro,))
        libro = db.obtener_uno()
        if not libro:
            print("❌ Libro no encontrado.")
            db.cerrar()
            return
        if not libro["disponible"]:
            print("❌ El libro no está disponible.")
            db.cerrar()
            return

        # Registrar préstamo
        fecha = datetime.now().date()
        db.ejecutar(
            "INSERT INTO prestamos (id_usuario, id_libro, fecha_prestamo, fecha_devolucion) VALUES (%s, %s, %s, NULL)",
            (id_usuario, id_libro, fecha)
        )
        db.ejecutar("UPDATE libros SET disponible = %s WHERE id = %s", (False, id_libro))
        db.confirmar()
        db.cerrar()
        log_evento(f"Préstamo registrado: Usuario {id_usuario} - Libro {id_libro}")
        print("✅ Préstamo registrado correctamente.")

    @staticmethod
    def devolver():
        try:
            id_prestamo = int(input("ID del préstamo: "))
        except ValueError:
            print("❌ ID inválido.")
            return

        db = ConexionBD()
        db.ejecutar("SELECT * FROM prestamos WHERE id = %s", (id_prestamo,))
        prestamo = db.obtener_uno()
        if not prestamo:
            print("❌ Préstamo no encontrado.")
            db.cerrar()
            return
        if prestamo["fecha_devolucion"]:
            print("❌ El libro ya fue devuelto.")
            db.cerrar()
            return

        fecha_dev = datetime.now().date()
        db.ejecutar("UPDATE prestamos SET fecha_devolucion = %s WHERE id = %s", (fecha_dev, id_prestamo))
        db.ejecutar("UPDATE libros SET disponible = %s WHERE id = %s", (True, prestamo["id_libro"]))
        db.confirmar()
        db.cerrar()
        log_evento(f"Devolución registrada: Préstamo {id_prestamo}")
        print("✅ Libro devuelto correctamente.")

    @staticmethod
    def listar_activos():
        db = ConexionBD()
        db.ejecutar("""
            SELECT p.id, u.nombre, l.titulo, p.fecha_prestamo 
            FROM prestamos p 
            JOIN usuarios u ON p.id_usuario = u.id 
            JOIN libros l ON p.id_libro = l.id 
            WHERE p.fecha_devolucion IS NULL
        """)
        prestamos = db.obtener_todos()
        if not prestamos:
            print("No hay préstamos activos.")
        else:
            for p in prestamos:
                print(f"[{p['id']}] {p['nombre']} - {p['titulo']} (Prestado el {p['fecha_prestamo']})")
        db.cerrar()

# ============================================================
# CLASE PRINCIPAL DEL SISTEMA (MENÚS)
# ============================================================
class SistemaBiblioteca:
    def menu_libros(self):
        while True:
            print("\n--- MENÚ LIBROS ---")
            print("1. Registrar libro")
            print("2. Listar libros")
            print("3. Buscar libro")
            print("4. Volver al menú principal")
            opcion = input("Selecciona una opción: ")
            if opcion == "1": Libro.registrar()
            elif opcion == "2": Libro.listar()
            elif opcion == "3": Libro.buscar()
            elif opcion == "4": break
            else: print("❌ Opción inválida.")

    def menu_usuarios(self):
        while True:
            print("\n--- MENÚ USUARIOS ---")
            print("1. Registrar usuario")
            print("2. Listar usuarios")
            print("3. Buscar usuario")
            print("4. Volver al menú principal")
            opcion = input("Selecciona una opción: ")
            if opcion == "1": Usuario.registrar()
            elif opcion == "2": Usuario.listar()
            elif opcion == "3": Usuario.buscar()
            elif opcion == "4": break
            else: print("❌ Opción inválida.")

    def menu_prestamos(self):
        while True:
            print("\n--- MENÚ PRÉSTAMOS ---")
            print("1. Registrar préstamo")
            print("2. Devolver libro")
            print("3. Ver préstamos activos")
            print("4. Volver al menú principal")
            opcion = input("Selecciona una opción: ")
            if opcion == "1": Prestamo.registrar()
            elif opcion == "2": Prestamo.devolver()
            elif opcion == "3": Prestamo.listar_activos()
            elif opcion == "4": break
            else: print("❌ Opción inválida.")

    def menu_principal(self):
        while True:
            print("\n===== SISTEMA DE BIBLIOTECA =====")
            print("1. Libros")
            print("2. Usuarios")
            print("3. Préstamos")
            print("4. Salir")
            opcion = input("Selecciona una opción: ")
            if opcion == "1": self.menu_libros()
            elif opcion == "2": self.menu_usuarios()
            elif opcion == "3": self.menu_prestamos()
            elif opcion == "4":
                print("👋 Saliendo del sistema...")
                break
            else:
                print("❌ Opción inválida.")

# ============================================================
# EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    sistema = SistemaBiblioteca()
    sistema.menu_principal()
