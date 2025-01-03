from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
from inventario import inventario_bp
from materiales import materiales_bp
import os

app = Flask(__name__)
app.secret_key = "khuger3894j"

app.register_blueprint(inventario_bp, url_prefix='/inventario')
app.register_blueprint(materiales_bp, url_prefix='/materiales')

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='constructora',
            ssl_disabled=True
        )
        return conn
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

@app.route('/')
def home():
    # Redirige a la ruta de registro
    return redirect('/usuarios/registro')

@app.route("/download-report")
def download_report():
    # Define la ruta del archivo Power BI
    file_path = os.path.join(os.getcwd(), 'Reporteconstructora.pbix')
    
    try:
        # Verifica si el archivo existe
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name="Reporteconstructora.pbix", mimetype="application/octet-stream")
        else:
            return "El archivo no se encontró.", 404
    except Exception as e:
        return str(e), 500

@app.route("/proyectos/eliminar", methods=['POST'])
def eliminar_proyecto():
    project_id = request.form['project_id']
    conn = get_db_connection()
    
    if conn:
        try:
            with conn.cursor() as cursor:
                # Eliminar el proyecto de la base de datos
                cursor.execute("DELETE FROM proyectos WHERE ID = %s", (project_id,))
                conn.commit()
                flash('Proyecto eliminado correctamente.', 'success')
                return redirect(url_for('ver_proyectos'))
        except Error as e:
            print(f"Error al eliminar el proyecto: {e}")
            flash('Error al eliminar el proyecto.', 'danger')
            return redirect(url_for('ver_proyectos'))
        finally:
            conn.close()
    else:
        flash('Error al conectar a la base de datos.', 'danger')
        return redirect(url_for('ver_proyectos'))


@app.route("/proyectos/leer")
def ver_proyectos():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT ID, Nombre FROM proyectos")
                proyectos = cursor.fetchall()
            return render_template("proyectos/leer.html", proyectos=proyectos)
        except Error as e:
            print(f"Error al obtener los proyectos: {e}")
            return "Error al obtener los proyectos."
        finally:
            conn.close()
    else:
        return "Error al conectar a la base de datos."

@app.route("/proyectos/detalles/<int:proyecto_id>")
def detalles_proyecto(proyecto_id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT p.Nombre, p.TipoProyecto, p.CondicionesTerreno, p.TamañoTerreno, 
                           p.NumeroTrabajadores, p.TiempoEstimado, p.PorcentajeGanancia, 
                           p.CostoTotal, p.Estado, u.Nombre AS Supervisor, p.IngresosEstimados
                    FROM proyectos p
                    LEFT JOIN usuarios u ON p.Supervisor_ID = u.ID
                    WHERE p.ID = %s
                """, (proyecto_id,))
                proyecto = cursor.fetchone()
            return proyecto if proyecto else {}, 200
        except Error as e:
            print(f"Error al obtener detalles del proyecto: {e}")
            return {}, 500
        finally:
            conn.close()
    else:
        return {}, 500


@app.route('/proyectos/actualizar', methods=['GET', 'POST'])
def actualizar_proyecto():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor(dictionary=True) as cursor:
                # Obtener lista de proyectos
                cursor.execute("SELECT ID, Nombre FROM Proyectos")
                proyectos = cursor.fetchall()

                # Obtener lista de usuarios
                cursor.execute("SELECT ID, Nombre FROM Usuarios")
                supervisores = cursor.fetchall()

                if request.method == 'POST':
                    # Recibir datos del formulario
                    proyecto_id = request.form['id']  # ID del proyecto a actualizar
                    nombre = request.form['nombre']
                    tipo_proyecto = request.form['tipo_proyecto']
                    condiciones_terreno = request.form['condiciones_terreno']
                    tamaño_terreno = request.form['tamaño_terreno']
                    numero_trabajadores = request.form['numero_trabajadores']
                    tiempo_estimado = request.form['tiempo_estimado']
                    costo_total = request.form['costo_total']
                    estado = request.form['estado']
                    supervisor_id = request.form['supervisor_id']
                    ingresos_estimados = request.form['ingresos_estimados']

                    # Actualizar los datos del proyecto en la base de datos
                    cursor.execute("""
                        UPDATE Proyectos 
                        SET Nombre = %s, TipoProyecto = %s, CondicionesTerreno = %s, 
                            TamañoTerreno = %s, NumeroTrabajadores = %s, TiempoEstimado = %s, 
                            CostoTotal = %s, Estado = %s, Supervisor_ID = %s, IngresosEstimados = %s
                        WHERE ID = %s
                    """, (nombre, tipo_proyecto, condiciones_terreno, tamaño_terreno,
                          numero_trabajadores, tiempo_estimado, costo_total, estado,
                          supervisor_id, ingresos_estimados, proyecto_id))
                    conn.commit()
                    return redirect('/menu_proyectos')

            return render_template('proyectos/actualizar.html', proyectos=proyectos, supervisores=supervisores)
        except Error as e:
            print(f"Error al interactuar con la base de datos: {e}")
            return "Error al procesar la solicitud."
        finally:
            conn.close()
    else:
        return "Error al conectar con la base de datos."



@app.route('/proyectos/crear', methods=['GET', 'POST'])
def crear_proyecto():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor(dictionary=True) as cursor:
                # Obtener lista de supervisores
                cursor.execute("SELECT ID, Nombre FROM Usuarios")
                supervisores = cursor.fetchall()

                if request.method == 'POST':
                    # Recibir datos del formulario
                    nombre = request.form['nombre']
                    tipo_proyecto = request.form['tipo_proyecto']
                    condiciones_terreno = request.form['condiciones_terreno']
                    tamaño_terreno = request.form['tamaño_terreno']
                    numero_trabajadores = request.form['numero_trabajadores']
                    tiempo_estimado = request.form['tiempo_estimado']
                    costo_total = request.form['costo_total']
                    estado = request.form['estado']
                    supervisor_id = request.form['supervisor']
                    ingresos_estimados = request.form['ingresos_estimados']

                    # Insertar datos en la tabla proyectos
                    cursor.execute("""
                        INSERT INTO Proyectos 
                        (Nombre, TipoProyecto, CondicionesTerreno, TamañoTerreno, 
                         NumeroTrabajadores, TiempoEstimado, CostoTotal, Estado, 
                         Supervisor_ID, IngresosEstimados) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (nombre, tipo_proyecto, condiciones_terreno, tamaño_terreno,
                          numero_trabajadores, tiempo_estimado, costo_total, estado,
                          supervisor_id, ingresos_estimados))
                    conn.commit()
                    return redirect('/menu_proyectos')

            return render_template('proyectos/crear.html', supervisores=supervisores)
        except Error as e:
            print(f"Error al interactuar con la base de datos: {e}")
            return "Error al procesar la solicitud."
        finally:
            conn.close()
    else:
        return "Error al conectar con la base de datos."
    
@app.route('/usuarios/registro', methods=['GET', 'POST'])
def registro_usuario():
    conn = get_db_connection()
    if not conn:
        return "Error al conectar a la base de datos."

    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        contraseña = request.form['contraseña']
        rol_id = request.form['rol_id']
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO usuarios (Nombre, Email, Contraseña, Rol_ID) VALUES (%s, %s, %s, %s)", 
                               (nombre, email, contraseña, rol_id))
                conn.commit()
                flash('Usuario registrado exitosamente.', 'success')
                return redirect(url_for('login_usuario'))
        except Error as e:
            print(f"Error al insertar el usuario: {e}")
            flash('Error al registrar usuario.', 'danger')
        finally:
            conn.close()
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT ID, Rol FROM roles")
            roles = cursor.fetchall()
        return render_template('usuarios/registro.html', roles=roles)
    except Error as e:
        print(f"Error al obtener roles: {e}")
        return "Error al obtener roles."
    finally:
        conn.close()

@app.route('/usuarios/login', methods=['GET', 'POST'])
def login_usuario():
    if request.method == 'POST':
        email = request.form['email']
        contraseña = request.form['contraseña']
        conn = get_db_connection()

        if conn:
            try:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT * FROM usuarios WHERE Email = %s", (email,))
                    usuario = cursor.fetchone()

                    # Aquí se valida la contraseña
                    if usuario and usuario['Contraseña'] == contraseña:  # Simple sin hash
                        flash('Inicio de sesión exitoso.', 'success')
                        session['usuario_id'] = usuario['ID']
                        session['rol_id'] = usuario['Rol_ID']
                        return redirect(url_for('menu_proyectos'))
                    else:
                        flash('Correo o contraseña incorrectos.', 'danger')
            except Error as e:
                print(f"Error al verificar el usuario: {e}")
                flash('Error al iniciar sesión.', 'danger')
            finally:
                conn.close()
        else:
            flash('Error al conectar con la base de datos.', 'danger')

    return render_template('usuarios/login.html')


@app.route('/menu_proyectos')
def menu_proyectos():
    # Verificar si el usuario ha iniciado sesión
    if 'usuario_id' in session:
        return render_template('proyectos/menu_proyectos.html')
    else:
        flash('Por favor, inicia sesión primero.', 'danger')
        return redirect(url_for('login_usuario'))

@app.route("/Roles/index")
def rol_index():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM Roles")
                datos = cursor.fetchall()
            return render_template('roles/index.html', lista=datos)
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return "Error al ejecutar la consulta."
        finally:
            conn.close()
    else:
        return "Error al conectar a la base de datos."

@app.route("/Roles/agregar", methods=["GET"])
def rol_agregar_get():
    return render_template("roles/agregar.html")

@app.route("/Roles/agregar", methods=["POST"])
def rol_agregar_post():
    conn = get_db_connection()
    if conn:
        try:
            v_rol = request.form['rol']
            if v_rol:
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO Roles (Rol) VALUES (%s)", (v_rol,))
                    conn.commit()
                return redirect(url_for('rol_index'))
            else:
                return "El rol no puede estar vacío."
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return "Error al ejecutar la consulta."
        finally:
            conn.close()
    else:
        return "Error al conectar a la base de datos."

@app.route("/Roles/editar/<string:id>", methods=["GET"])
def rol_editar_GET(id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM Roles WHERE ID=%s", (id,))
                roll = cursor.fetchone()
            if roll:
                return render_template("roles/editar.html", roll=roll)
            else:
                return "Rol no encontrado."
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return "Error al ejecutar la consulta."
        finally:
            conn.close()
    else:
        return "Error al conectar a la base de datos."

@app.route("/Roles/editar/<string:id>", methods=["POST"])
def rol_editar_POST(id):
    v_rol = request.form['rol']
    conn = get_db_connection()
    if conn:
        try:
            if v_rol:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE Roles SET Rol=%s WHERE ID=%s", (v_rol, id))
                    conn.commit()
                return redirect(url_for('rol_index'))
            else:
                return "El rol no puede estar vacío."
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return "Error al ejecutar la consulta."
        finally:
            conn.close()
    else:
        return "Error al conectar a la base de datos."

@app.route("/Roles/eliminar/<string:id>", methods=["POST", "GET"])
def rol_eliminar(id):
    conn = get_db_connection()
    if conn:
        if request.method == 'GET':
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM Roles WHERE ID=%s", (id,))
                    roll = cursor.fetchone()
                if roll:
                    return render_template("roles/eliminar.html", roll=roll)
                else:
                    return "Rol no encontrado."
            except Error as e:
                print(f"Error al ejecutar la consulta: {e}")
                return "Error al ejecutar la consulta."
            finally:
                conn.close()

        if request.method == 'POST':
            try:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM Roles WHERE ID=%s", (id,))
                    conn.commit()
                return redirect(url_for('rol_index'))
            except Error as e:
                print(f"Error al ejecutar la consulta: {e}")
                return "Error al ejecutar la consulta."
            finally:
                conn.close()
    else:
        return "Error al conectar a la base de datos."
    
@app.route("/Usuarios/index")
def usuario_index():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT u.ID, u.Nombre, u.Email, u.Contraseña, r.Rol 
                    FROM Usuarios u
                    JOIN Roles r ON u.Rol_ID = r.ID
                """)
                datos = cursor.fetchall()
            return render_template('usuarios/index.html', lista=datos)
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return "Error al ejecutar la consulta."
        finally:
            conn.close()
    else:
        return "Error al conectar a la base de datos."

@app.route("/Usuarios/agregar", methods=["GET"])
def usuario_agregar_get():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM Roles")
                roles = cursor.fetchall()

                cursor.execute("SELECT * FROM Usuarios")
                usuarios = cursor.fetchall()

            return render_template("usuarios/agregar.html", roles=roles, usuarios=usuarios)
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return "Error al ejecutar la consulta."
        finally:
            conn.close()
    else:
        return "Error al conectar a la base de datos."

@app.route("/Usuarios/agregar", methods=["POST"])
def usuario_agregar_post():
    conn = get_db_connection()
    if conn:
        try:
            v_nombre = request.form['nombre']
            v_email = request.form['email']
            v_contraseña = request.form['contraseña']
            v_rol_id = request.form['rol']
            if v_nombre and v_email and v_contraseña:
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO Usuarios (Nombre, Email, Contraseña, Rol_ID) VALUES (%s, %s, %s, %s)",
                                   (v_nombre, v_email, v_contraseña, v_rol_id))
                    conn.commit()
                return redirect(url_for('usuario_index'))
            else:
                return "Todos los campos son requeridos."
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return "Error al ejecutar la consulta."
        finally:
            conn.close()
    else:
        return "Error al conectar a la base de datos."

@app.route("/Usuarios/editar/<string:id>", methods=["GET"])
def usuario_editar_GET(id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM Roles")
                roles = cursor.fetchall()
                
                cursor.execute("SELECT * FROM Usuarios WHERE ID=%s", (id,))
                usu = cursor.fetchone()
            if usu:
                return render_template("usuarios/editar.html", roles=roles, usu=usu)
            else:
                return "Usuario no encontrado."
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return "Error al ejecutar la consulta."
        finally:
            conn.close()
    else:
        return "Error al conectar a la base de datos."

@app.route("/Usuarios/editar/<string:id>", methods=["POST"])
def usuario_editar_POST(id):
    
    conn = get_db_connection()
    if conn:
        try:
            v_nombre = request.form['nombre']
            v_email = request.form['email']
            v_contraseña = request.form['contraseña']
            v_rol_id = request.form['rol']
            
            if v_nombre and v_email and v_contraseña:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE Usuarios SET Nombre=%s, Email=%s, Contraseña=%s, Rol_ID=%s WHERE ID=%s",
                                   (v_nombre, v_email, v_contraseña, v_rol_id, id))
                    conn.commit()
                return redirect(url_for('usuario_index'))
            else:
                return "Todos los campos son requeridos."
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return "Error al ejecutar la consulta."
        finally:
            conn.close()
    else:
        return "Error al conectar a la base de datos."

@app.route("/Usuarios/eliminar/<string:id>", methods=["POST", "GET"])
def usuario_eliminar(id):
    conn = get_db_connection()
    if conn:
        if request.method == 'GET':
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM Usuarios WHERE ID = %s", (id,))
                    usu = cursor.fetchone()

                    if usu:
                        cursor.execute("SELECT Rol FROM Roles WHERE ID = %s", (usu[4],))
                        rol = cursor.fetchone()

                        if rol:
                            return render_template("usuarios/eliminar.html", usu=usu, rol=rol[0])
                        else:
                            return "Rol no encontrado."
                    else:
                        return "Usuario no encontrado."
            except Error as e:
                print(f"Error al ejecutar la consulta: {e}")
                return "Error al ejecutar la consulta."
            finally:
                conn.close()

        if request.method == 'POST':
            try:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM Usuarios WHERE ID = %s", (id,))
                    conn.commit()
                return redirect(url_for('usuario_index'))
            except Error as e:
                print(f"Error al ejecutar la consulta: {e}")
                return "Error al ejecutar la consulta."
            finally:
                conn.close()
    else:
        return "Error al conectar a la base de datos."
    
@app.route("/Proveedores/index")
def proveedor_index():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM Proveedores")
                datos = cursor.fetchall()
            return render_template('proveedores/index.html', lista=datos)
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return "Error al ejecutar la consulta."
        finally:
            conn.close()
    else:
        return "Error al conectar a la base de datos."

@app.route("/Proveedores/agregar", methods=["GET"])
def proveedor_agregar_get():
    return render_template("proveedores/agregar.html")

@app.route("/Proveedores/agregar", methods=["POST"])
def proveedor_agregar_post():
    conn = get_db_connection()
    if conn:
        try:
            v_nombre = request.form['nombre']
            v_contacto = request.form['contacto']
            v_telefono = request.form['telefono']
            v_email = request.form['email']
            v_direccion = request.form['direccion']
            if v_nombre:
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO Proveedores (Nombre, Contacto, Telefono, Email, Direccion) VALUES (%s, %s, %s, %s, %s)", (v_nombre, v_contacto, v_telefono, v_email, v_direccion))
                    conn.commit()
                return redirect(url_for('proveedor_index'))
            else:
                return "El proveedor no puede estar vacío."
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return "Error al ejecutar la consulta."
        finally:
            conn.close()
    else:
        return "Error al conectar a la base de datos."

@app.route("/Proveedores/editar/<string:id>", methods=["GET"])
def proveedor_editar_GET(id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM Proveedores WHERE ID=%s", (id,))
                prov = cursor.fetchone()
            if prov:
                return render_template("proveedores/editar.html", prov=prov)
            else:
                return "Proveedor no encontrado."
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return "Error al ejecutar la consulta."
        finally:
            conn.close()
    else:
        return "Error al conectar a la base de datos."

@app.route("/Proveedores/editar/<string:id>", methods=["POST"])
def proveedor_editar_POST(id):
    v_nombre = request.form['nombre']
    v_contacto = request.form['contacto']
    v_telefono = request.form['telefono']
    v_email = request.form['email']
    v_direccion = request.form['direccion']
    conn = get_db_connection()
    if conn:
        try:
            if v_nombre:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE Proveedores SET Nombre=%s, Contacto=%s, Telefono=%s, Email=%s, Direccion=%s WHERE ID=%s", (v_nombre, v_contacto, v_telefono, v_email, v_direccion, id))
                    conn.commit()
                return redirect(url_for('proveedor_index'))
            else:
                return "El Proveedor no puede estar vacío."
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return "Error al ejecutar la consulta."
        finally:
            conn.close()
    else:
        return "Error al conectar a la base de datos."

@app.route("/Proveedores/eliminar/<string:id>", methods=["POST", "GET"])
def proveedor_eliminar(id):
    conn = get_db_connection()
    if conn:
        if request.method == 'GET':
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM Proveedores WHERE ID=%s", (id,))
                    prov = cursor.fetchone()
                if prov:
                    return render_template("proveedores/eliminar.html", prov=prov)
                else:
                    return "Proveedor no encontrado."
            except Error as e:
                print(f"Error al ejecutar la consulta: {e}")
                return "Error al ejecutar la consulta."
            finally:
                conn.close()

        if request.method == 'POST':
            try:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM Proveedores WHERE ID=%s", (id,))
                    conn.commit()
                return redirect(url_for('proveedor_index'))
            except Error as e:
                print(f"Error al ejecutar la consulta: {e}")
                return "Error al ejecutar la consulta."
            finally:
                conn.close()
    else:
        return "Error al conectar a la base de datos."

if __name__ == '__main__':
    app.run(debug=True)
