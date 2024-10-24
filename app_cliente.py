from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
import pandas as pd
from io import BytesIO
from flask import send_file
from flask import Flask, session
import io
import datetime

app_cliente = Flask(__name__)
app_cliente.secret_key = 'your_secret_key'

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="proyecto_is1"
        )
        if connection.is_connected():
            print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

def insert_user( nombre, apellido, fecha_nacimiento, email,telefono,direccion,fecha_registro, tipo, documento):
    connection = create_connection()
    if connection is None:
        return
    cursor = connection.cursor()
    query = "INSERT INTO cliente ( nombre, apellido, fecha_nacimiento, email,telefono,direccion,fecha_registro, tipo, documento) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    values =( nombre, apellido, fecha_nacimiento, email,telefono,direccion,fecha_registro, tipo, documento)
    try:
        cursor.execute(query, values)
        connection.commit()
        return True
    except Error as e:
        print(f"The error '{e}' occurred")
        return False
    finally:
        cursor.close()
        connection.close()

def get_cliente():
    connection = create_connection()
    if connection is None:
        return []
    cursor = connection.cursor()
    query = "SELECT * FROM cliente"
    try:
        cursor.execute(query)
        cliente = cursor.fetchall()
        return cliente
    except Error as e:
        print(f"The error '{e}' occurred")
        return []
    finally:
        cursor.close()
        connection.close()

def get_cliente_by_id(id_cliente):
    connection = create_connection()
    if connection is None:
        return None
    cursor = connection.cursor()
    query = "SELECT * FROM cliente WHERE id_cliente = %s"
    try:
        cursor.execute(query, (id_cliente,))
        cliente = cursor.fetchone()
        return cliente
    except Error as e:
        print(f"The error '{e}' occurred")
        return None
    finally:
        cursor.close()
        connection.close()

def update_user(id_cliente, nombre, apellido, fecha_nacimiento, email,telefono,direccion,fecha_registro, tipo, documento):
    connection = create_connection()
    if connection is None:
        return False
    cursor = connection.cursor()
    query = "UPDATE cliente SET  nombre = %s, apellido = %s, fecha_nacimiento = %s, email = %s,telefono = %s,direccion = %s,fecha_registro = %s ,tipo = %s, documento = %s WHERE id_cliente = %s"
    values = ( nombre, apellido, fecha_nacimiento, email,telefono,direccion,fecha_registro, tipo, documento,id_cliente)
    try:
        cursor.execute(query, values)
        connection.commit()
        return True
    except Error as e:
        print(f"The error '{e}' occurred")
        return False
    finally:
        cursor.close()
        connection.close()

def delete_user(id_cliente):
    connection = create_connection()
    if connection is None:
        return False
    cursor = connection.cursor()
    query = "DELETE FROM cliente WHERE id_cliente = %s"
    try:
        cursor.execute(query, (id_cliente,))
        connection.commit()
        return True
    except Error as e:
        print(f"The error '{e}' occurred")
        return False
    finally:
        cursor.close()
        connection.close()

def search_users(search_query):
    connection = create_connection()
    if connection is None:
        return []
    cursor = connection.cursor()
    query = "SELECT * FROM cliente WHERE id_cliente LIKE %s OR nombre LIKE %s OR apellido LIKE %s OR fecha_nacimiento LIKE %s OR email LIKE %s OR telefono LIKE %s OR direccion LIKE %s  OR fecha_registro LIKE %s OR tipo LIKE %s OR documento LIKE %s"
    values = (f'%{search_query}%', f'%{search_query}%',f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}', f'%{search_query}',f'%{search_query}',f'%{search_query}00')
    try:
        cursor.execute(query, values)
        cliente = cursor.fetchall()
        return cliente
    except Error as e:
        print(f"The error '{e}' occurred")
        return []
    finally:
        cursor.close()
        connection.close()

def get_historico_clientes(page, per_page):
    connection = create_connection()
    if connection is None:
        return [], 0
    cursor = connection.cursor()
    offset = (page - 1) * per_page
    query = "SELECT SQL_CALC_FOUND_ROWS * FROM historicos_clientes LIMIT %s OFFSET %s"
    try:
        cursor.execute(query, (per_page, offset))
        historico_clientes = cursor.fetchall()
        cursor.execute("SELECT FOUND_ROWS()")
        total_historico_clientes = cursor.fetchone()[0]
        return historico_clientes, total_historico_clientes
    except Error as e:
        print(f"The error '{e}' occurred")
        return [], 0
    finally:
        cursor.close()
        connection.close()

@app_cliente.template_filter('format_dni')
def format_dni(dni):
    if dni and len(dni) == 13:
        return f"{dni[:4]}-{dni[4:8]}-{dni[8:]}"
    return dni

@app_cliente.route('/historico_clientes')
def historico_clientes():
    page = request.args.get('page', 1, type=int)
    per_page = int(request.args.get('per_page', 10))
    historicos, total_historicos = get_historico_clientes(page, per_page)

    total_pages = (total_historicos + per_page - 1) // per_page
    return render_template('historico_clientes.html', historicos=historicos, page=page, per_page=per_page, total_historicos=total_historicos, total_pages=total_pages)

@app_cliente.route('/')
def index_cliente():
    return render_template('index_cliente.html')

@app_cliente.route('/cliente')
def cliente():
    search_query = request.args.get('search')
    if search_query:
        cliente = search_users(search_query)
    else:
        cliente = get_cliente()
    return render_template('cliente.html', cliente=cliente, search_query=search_query)

@app_cliente.route('/submit', methods=['POST'])
def submit():
    
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    fecha_nacimiento = request.form['fecha_nacimiento']
    email = request.form['email']
    telefono = request.form['telefono']
    direccion = request.form['direccion']
    fecha_registro = request.form['fecha_registro']
    tipo = request.form['tipo']
    documento = request.form['documento']

    if not  nombre or not apellido or not fecha_nacimiento or not email or not telefono or not direccion or not fecha_registro or not tipo or not documento:
        flash('Todos los campos son necesarios!')
        return redirect(url_for('index_cliente'))

    if insert_user( nombre, apellido, fecha_nacimiento, email,telefono,direccion,fecha_registro, tipo, documento):
        flash('Cliente insertado!')
    else:
        flash('Error insertando el cliente.')
    
    return redirect(url_for('index_cliente'))

# Nueva función para generar y descargar el archivo Excel
@app_cliente.route('/descargar_excel')
def descargar_excel():
    cliente = get_cliente()  # Obtener los datos de la base de datos

    if not cliente:
        flash('No hay clientes para descargar.')
        return redirect(url_for('cliente'))

    # Crear un DataFrame con los datos de los clientes
    columnas = ['ID', 'Nombre', 'Apellido', 'Fecha Nacimiento', 'Email', 'Telefono', 'Direccion', 'Fecha Registro', 'Tipo', 'Documento']
    df = pd.DataFrame(cliente, columns=columnas)

    # Obtener la fecha y hora actual
    fecha_hora_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Obtener los datos del usuario desde la sesión
    usuario = f"{session.get('primer_nombre', 'Usuario desconocido')} {session.get('primer_apellido', '')}"

    # Crear un archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Escribir los datos de la tabla
        df.to_excel(writer, sheet_name='Clientes', index=False, startrow=4)  # Los datos comenzarán en la fila 5 (índice 4)

        # Obtener el workbook y worksheet para escribir metadatos
        workbook = writer.book
        worksheet = writer.sheets['Clientes']

        # Agregar metadata en las primeras filas
        worksheet.write('A1', 'Listado de Clientes')
        worksheet.write('A2', f'Fecha y hora: {fecha_hora_actual}')
        worksheet.write('A3', f'Impreso por: {usuario}')

        # Ajustar el ancho de las columnas
        worksheet.set_column(0, len(columnas) - 1, 20)

    # Preparar el archivo para descargar
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name='clientes.xlsx')

@app_cliente.route('/edit_cliente/<int:id_cliente>', methods=['GET', 'POST'])
def edit_cliente(id_cliente):
    if request.method == 'POST':
        
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        fecha_nacimiento = request.form['fecha_nacimiento']
        email = request.form['email']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        fecha_registro = request.form['fecha_registro']
        tipo = request.form['tipo']
        documento = request.form['documento']

        if not id_cliente or not nombre or not apellido or not fecha_nacimiento or not email or not telefono or not direccion or not fecha_registro or not tipo or not documento:
            flash('All fields are required!')
            return redirect(url_for('edit_cliente', id_cliente=id_cliente))

        if update_user(id_cliente, nombre, apellido, fecha_nacimiento, email,telefono,direccion,fecha_registro, tipo, documento):
            flash('Cliente actualizado!')
        else:
            flash('Error actualizando el cliente.')
        
        return redirect(url_for('cliente'))

    cliente = get_cliente_by_id(id_cliente)
    if cliente is None:
        flash('Product not found!')
        return redirect(url_for('cliente'))
    return render_template('edit_cliente.html', cliente=cliente)

@app_cliente.route('/eliminar_cliente/<int:id_cliente>', methods=['GET', 'POST'])
def eliminar_cliente(id_cliente):
    if request.method == 'POST':
        if delete_user(id_cliente):
            flash('Product deleted successfully!')
        else:
            flash('An error occurred while deleting the product.')
        return redirect(url_for('cliente'))

    cliente = get_cliente_by_id(id_cliente)
    if cliente is None:
        flash('Product not found!')
        return redirect(url_for('cliente'))
    return render_template('eliminar_cliente.html', cliente=cliente)

if __name__ == '__main__':
    app_cliente.run(debug=True,port=5004)
