from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from mysql.connector import Error
from decimal import Decimal

app_detalle_p = Flask(__name__)
app_detalle_p.secret_key = 'your_secret_key'

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
            print("Conexión exitosa a la base de datos MySQL")
    except Error as e:
        print(f"Error '{e}' ocurrió")
    return connection

from decimal import Decimal

def insert_or_update_detalle(id_pedido, id_producto, cantidad, precio_unitario, subtotal, id_impuesto, total):
    connection = create_connection()
    cursor = connection.cursor()

    try:
        # Convertir el subtotal y el total a Decimal
        subtotal = Decimal(subtotal)
        total = Decimal(total)

        # Verificar si ya existe el producto en el pedido
        query = """SELECT cantidad, subtotal FROM Detalle_de_compra_proveedor 
                   WHERE id_pedido = %s AND id_producto = %s"""
        cursor.execute(query, (id_pedido, id_producto))
        existing_detail = cursor.fetchone()

        if existing_detail:
            # Convertir los valores existentes a Decimal
            cantidad_existente = Decimal(existing_detail[0])
            subtotal_existente = Decimal(existing_detail[1])

            # Sumar la nueva cantidad y recalcular el subtotal
            nueva_cantidad = cantidad_existente + Decimal(cantidad)
            nuevo_subtotal = subtotal_existente + subtotal

            # Recalcular el total con el nuevo subtotal y el impuesto
            tasa_impuesto_query = "SELECT tasa_impuesto FROM impuesto WHERE id_impuesto = %s"
            cursor.execute(tasa_impuesto_query, (id_impuesto,))
            tasa_impuesto = Decimal(cursor.fetchone()[0]) / Decimal(100)
            
            nuevo_total = nuevo_subtotal + (nuevo_subtotal * tasa_impuesto)

            # Actualizar el registro existente
            update_query = """UPDATE Detalle_de_compra_proveedor
                              SET cantidad = %s, subtotal = %s, total = %s
                              WHERE id_pedido = %s AND id_producto = %s"""
            cursor.execute(update_query, (nueva_cantidad, nuevo_subtotal, nuevo_total, id_pedido, id_producto))
        else:
            # Si el producto no existe, lo insertamos
            insert_query = """INSERT INTO Detalle_de_compra_proveedor
                              (id_pedido, id_producto, cantidad, precio_unitario, subtotal, id_impuesto, total)
                              VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(insert_query, (id_pedido, id_producto, cantidad, precio_unitario, subtotal, id_impuesto, total))

        connection.commit()
        return True

    except Error as e:
        print(f"Error al insertar o actualizar el detalle: {str(e)}")
        return False

    finally:
        cursor.close()
        connection.close()




def get_detalles(page, per_page):
    connection = create_connection()
    if connection is None:
        return [], 0
    cursor = connection.cursor()
    offset = (page - 1) * per_page
    query = """
    SELECT SQL_CALC_FOUND_ROWS d.id_detalle, p.id_pedido, pr.nombre AS producto, d.cantidad, d.precio_unitario, d.subtotal, i.tasa_impuesto, d.total
    FROM detalle_de_compra_proveedor d
    JOIN pedido_de_compra_proveedor p ON d.id_pedido = p.id_pedido
    JOIN producto pr ON d.id_producto = pr.id_producto
    JOIN impuesto i ON d.id_impuesto = i.id_impuesto
    LIMIT %s OFFSET %s
    """
    try:
        cursor.execute(query, (per_page, offset))
        detalles_p = cursor.fetchall()
        cursor.execute("SELECT FOUND_ROWS()")
        total_detalles = cursor.fetchone()[0]
        return detalles_p, total_detalles
    except Error as e:
        print(f"Error '{e}' ocurrió")
        return [], 0
    finally:
        cursor.close()
        connection.close()

@app_detalle_p.route('/get_inventario/<int:id_producto>', methods=['GET'])
def get_inventario(id_producto):
    connection = create_connection()
    if connection is None:
        return {"cantidad_en_stock": 0, "stock_maximo": 1000}, 500
    cursor = connection.cursor()
    query = "SELECT cantidad_en_stock FROM inventario WHERE id_producto = %s"
    try:
        cursor.execute(query, (id_producto,))
        result = cursor.fetchone()
        if result:
            cantidad_en_stock = int(result[0])
            return {"cantidad_en_stock": cantidad_en_stock, "stock_maximo": 1000}, 200
        else:
            return {"cantidad_en_stock": 0, "stock_maximo": 1000}, 404
    except Error as e:
        print(f"Error '{e}' ocurrió")
        return {"cantidad_en_stock": 0, "stock_maximo": 1000}, 500
    finally:
        cursor.close()
        connection.close()


def get_detalle_by_id(id_detalle):
    connection = create_connection()
    if connection is None:
        return None
    cursor = connection.cursor()
    query = "SELECT * FROM detalle_de_compra_proveedor WHERE id_detalle = %s"
    try:
        cursor.execute(query, (id_detalle,))
        detalle_p = cursor.fetchone()
        return detalle_p
    except Error as e:
        print(f"Error '{e}' ocurrió")
        return None
    finally:
        cursor.close()
        connection.close()

def update_detalle(id_detalle, id_pedido, id_producto, cantidad, precio_unitario, subtotal, id_impuesto, total):
    connection = create_connection()
    if connection is None:
        return False
    cursor = connection.cursor()
    query = """
    UPDATE detalle_de_compra_proveedor
    SET id_pedido = %s, id_producto = %s, cantidad = %s, precio_unitario = %s, subtotal = %s, id_impuesto = %s, total = %s
    WHERE id_detalle = %s
    """
    values = (id_pedido, id_producto, cantidad, precio_unitario, subtotal, id_impuesto, total, id_detalle)
    try:
        cursor.execute(query, values)
        connection.commit()
        return True
    except Error as e:
        print(f"Error '{e}' ocurrió")
        return False
    finally:
        cursor.close()
        connection.close()

def delete_detalle(id_detalle):
    connection = create_connection()
    if connection is None:
        return False
    cursor = connection.cursor()
    query = "DELETE FROM detalle_de_compra_proveedor WHERE id_detalle = %s"
    try:
        cursor.execute(query, (id_detalle,))
        connection.commit()
        return True
    except Error as e:
        print(f"Error '{e}' ocurrió")
        return False
    finally:
        cursor.close()
        connection.close()

@app_detalle_p.route('/')
def index_detalle_p():
    connection = create_connection()
    if connection is None:
        return render_template('index_detalle_p.html', pedidos=[], productos=[], impuestos=[], max_pedido=None)

    cursor = connection.cursor()

    # Obtener todos los pedidos
    cursor.execute("SELECT id_pedido FROM pedido_de_compra_proveedor")
    pedidos = cursor.fetchall()

    # Obtener el máximo id_pedido
    cursor.execute("SELECT MAX(id_pedido) FROM pedido_de_compra_proveedor")
    max_pedido = cursor.fetchone()[0]

    # Obtener productos del proveedor del máximo pedido
    cursor.execute("""
        SELECT p.id_producto, p.nombre 
        FROM producto p
        JOIN pedido_de_compra_proveedor pp ON p.id_proveedor = pp.id_proveedor
        WHERE pp.id_pedido = %s
    """, (max_pedido,))
    productos = cursor.fetchall()

    # Obtener todos los impuestos
    cursor.execute("SELECT id_impuesto, tasa_impuesto FROM impuesto")
    impuestos = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('index_detalle_p.html', pedidos=pedidos, productos=productos, impuestos=impuestos, max_pedido=max_pedido)


@app_detalle_p.route('/detalles_p')
def detalles_p():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    detalles_p, total_detalles = get_detalles(page, per_page)
    total_pages = (total_detalles + per_page - 1) // per_page
    return render_template('detalles_p.html', detalles_p=detalles_p, page=page, per_page=per_page, total_detalles=total_detalles, total_pages=total_pages)

@app_detalle_p.route('/submit_detalle', methods=['POST'])
def submit_detalle():
    # Obtener datos del formulario
    id_pedido = request.form['id_pedido']
    id_producto = request.form['id_producto']
    cantidad = float(request.form['cantidad'])
    precio_unitario = float(request.form['precio_unitario'])
    id_impuesto = request.form['id_impuesto']
    
    # Calcular el subtotal (cantidad * precio_unitario)
    subtotal = cantidad * precio_unitario

    # Obtener la tasa de impuesto desde la base de datos
    connection = create_connection()
    cursor = connection.cursor()
    
    try:
        # Consulta para obtener la tasa de impuesto
        query_impuesto = "SELECT tasa_impuesto FROM impuesto WHERE id_impuesto = %s"
        cursor.execute(query_impuesto, (id_impuesto,))
        result = cursor.fetchone()

        if result is None:
            flash('Impuesto no encontrado.')
            return redirect(url_for('index_detalle_p'))
        
        # Cálculo del total (subtotal + impuesto)
        tasa_impuesto = float(result[0]) / 100
        total = subtotal + (subtotal * tasa_impuesto)
        
        # Insertar o actualizar el detalle de compra
        if insert_or_update_detalle(id_pedido, id_producto, cantidad, precio_unitario, subtotal, id_impuesto, total):
            flash('Detalle insertado o actualizado exitosamente!')
        else:
            flash('Error al insertar o actualizar el detalle.')
    
    except Error as e:
        flash(f"Ocurrió un error: {str(e)}")
        return redirect(url_for('index_detalle_p'))
    
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('index_detalle_p'))

@app_detalle_p.route('/edit_detalle_p/<int:id_detalle>', methods=['GET', 'POST'])
def edit_detalle_p(id_detalle):
    if request.method == 'POST':
        id_pedido = request.form['id_pedido']
        id_producto = request.form['id_producto']
        cantidad = float(request.form['cantidad'])
        precio_unitario = float(request.form['precio_unitario'])
        subtotal = float(request.form['subtotal'])
        id_impuesto = request.form['id_impuesto']
        total = float(request.form['total'])

        if not id_pedido or not id_producto or not cantidad or not precio_unitario or not subtotal or not id_impuesto or not total:
            flash('Todos los campos son requeridos!')
            return redirect(url_for('edit_detalle_p', id_detalle=id_detalle))

        if update_detalle(id_detalle, id_pedido, id_producto, cantidad, precio_unitario, subtotal, id_impuesto, total):
            flash('detalle_p actualizado exitosamente!')
        else:
            flash('Ocurrió un error al actualizar el detalle_p.')
        
        return redirect(url_for('detalles_p'))

    detalle_p = get_detalle_by_id(id_detalle)
    if detalle_p is None:
        flash('detalle_p no encontrado!')
        return redirect(url_for('detalles_p'))

    connection = create_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT id_pedido FROM pedido_de_compra_proveedor")
    pedidos = cursor.fetchall()

    cursor.execute("SELECT id_producto, nombre FROM producto")
    productos = cursor.fetchall()

    cursor.execute("SELECT id_impuesto, tasa_impuesto FROM impuesto")
    impuestos = cursor.fetchall()
    
    cursor.close()
    connection.close()

    return render_template('edit_detalle_p.html', detalle_p=detalle_p, pedidos=pedidos, productos=productos, impuestos=impuestos)

@app_detalle_p.route('/eliminar_detalle_p/<int:id_detalle>', methods=['GET', 'POST'])
def eliminar_detalle_p(id_detalle):
    if request.method == 'POST':
        if delete_detalle(id_detalle):
            flash('detalle_p eliminado exitosamente!')
        else:
            flash('Ocurrió un error al eliminar el detalle_p.')
        return redirect(url_for('detalles_p'))

    detalle_p = get_detalle_by_id(id_detalle)
    if detalle_p is None:
        flash('detalle_p no encontrado!')
        return redirect(url_for('detalles_p'))

    return render_template('eliminar_detalle_p.html', detalle_p=detalle_p)

@app_detalle_p.route('/get_precio/<int:id_producto>', methods=['GET'])
def get_precio(id_producto):
    connection = create_connection()
    if connection is None:
        return {"precio_unitario": 0, "cantidad_en_stock": 0, "stock_maximo": 0}, 500
    cursor = connection.cursor()
    query = """
        SELECT p.original_precio, i.cantidad_en_stock, i.stock_maximo 
        FROM producto p 
        JOIN inventario i ON p.id_producto = i.id_producto 
        WHERE p.id_producto = %s
    """
    try:
        cursor.execute(query, (id_producto,))
        result = cursor.fetchone()
        if result:
            precio_unitario, cantidad_en_stock, stock_maximo = result
            return {"precio_unitario": float(precio_unitario), "cantidad_en_stock": int(cantidad_en_stock), "stock_maximo": int(stock_maximo)}, 200
        else:
            return {"precio_unitario": 0, "cantidad_en_stock": 0, "stock_maximo": 0}, 404
    except Error as e:
        print(f"Error '{e}' ocurrió")
        return {"precio_unitario": 0, "cantidad_en_stock": 0, "stock_maximo": 0}, 500
    finally:
        cursor.close()
        connection.close()


if __name__ == '__main__':
    app_detalle_p.run(debug=True,port=5022)
