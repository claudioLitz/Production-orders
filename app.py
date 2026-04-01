# ============================================================
# app.py – Back-end Flask of production orders system
# SENAI Jaraguá do Sul – Técnico em Cibersistemas para Automação
# ============================================================

import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from database import init_db, get_connection

# Create an instance of Flask application
# __name__ tells Flask where to search resources (templates, static, etc.)
app = Flask(__name__, static_folder='static', static_url_path='')

# Enable CORS – allows the front-end to make requests to the API without browser blocks
CORS(app)

# ── ROUTE 1: Main page ──────────────────────────────────
@app.route('/')
def index():
    """Serves the index.html file from the static folder."""
    return app.send_static_file('index.html')


# ── ROUTE 2: API stats ──────────────────────────────────
@app.route('/status')
def status():
    """Health check route with detailed information."""
    # Counts how many orders exist in the database
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM ordens')
    result = cursor.fetchone()
    conn.close()
    
    return jsonify({
        "status": "online",
        "sistema": "Production Orders System",
        "versao": "1.0.0",
        "total_ordens": result["total"],
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


# ── ROUTE 3: List all orders (GET) ───────────────────
@app.route('/ordens', methods=['GET'])
def list_orders():
    # request.args accesses query string parameters
    # Ex: /ordens?status=Pending → status_filter = 'Pending'
    status_filter = request.args.get('status')
    conn = get_connection()
    cursor = conn.cursor()
    
    if status_filter:
        cursor.execute('SELECT * FROM ordens WHERE status = ? ORDER BY id DESC', (status_filter,) )
    else:
        cursor.execute('SELECT * FROM ordens ORDER BY id DESC')
        
    orders = cursor.fetchall()
    conn.close()
    
    return jsonify([dict(o) for o in orders])


# ── ROUTE 4: Fetch a specific order by ID (GET) ───
@app.route('/ordens/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """
    Fetches a single production order by its ID.
    URL Parameters:
    order_id (int): ID of the order to be fetched.
    Returns:
    200 + Order JSON, if found.
    404 + error message, if it does not exist.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # The '?' is safely replaced by the order_id value
    cursor.execute('SELECT * FROM ordens WHERE id = ?', (order_id,))
    order = cursor.fetchone() # fetchone() returns a single record or None
    conn.close()
    
    # If the ID does not exist, return 404
    if order is None:
        return jsonify({'erro': f'Order {order_id} not found.'}), 404

    return jsonify(dict(order)), 200


# ── ROUTE 5: Create new production order (POST) ─────────
@app.route('/ordens', methods=['POST'])
def create_order():
    """
    Creates a new production order from the sent JSON data.
    
    Expected Body (JSON):
        produto (str):      Product name. Required.
        quantidade (int):   Quantity of parts. Required, > 0.
        status (str):       Optional. Default: 'Pending'.
    
    Returns:
    201 + Created order JSON, on success.
    400 + error message, if invalid data.
    """
    data = request.get_json()
    
    # ── Input validations ───────────────────────────────
    # Check if the body was sent and is a valid JSON
    if not data:
        return jsonify({'erro': 'Missing or invalid request body.'}), 400
    
    # Check required field 'produto'
    product_val = data.get('produto', '').strip()
    if not product_val:
        return jsonify({'erro': 'Field "produto" is required and cannot be empty.'}), 400
    
    # Check required field 'quantidade'
    quantity_val = data.get('quantidade')
    if quantity_val is None:
        return jsonify({'erro': 'Field "quantidade" is required.'}), 400
    
    # Check if quantity is a positive integer
    try:
        quantity_val = int(quantity_val)
        if quantity_val <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'erro': 'Field "quantidade" must be a positive integer.'}), 400
    
    # Status is optional; uses 'Pending' if not provided
    valid_statuses = ['Pending', 'In working', 'Done']
    status_val = data.get('status', 'Pending')
    
    if status_val not in valid_statuses:
        return jsonify({'erro': f'Invalid status. Use: {valid_statuses}'}), 400

    # ── Database insertion ───────────────────────────────────
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO ordens (produto, quantidade, status) VALUES (?, ?, ?)',
        (product_val, quantity_val, status_val)
    )
    conn.commit()
    
    # Retrieve the automatically generated ID from the database
    new_id = cursor.lastrowid
    conn.close()
    
    # Fetch the newly created record to return it completely
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ordens WHERE id = ?', (new_id,))
    new_order = cursor.fetchone()
    conn.close()

    # Returns 201 Created with the full record
    return jsonify(dict(new_order)), 201


# ── ROUTE 6: Update status of an order (PUT) ───────────────
@app.route('/ordens/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    """
    Updates the status of an existing production order.
    URL Parameters:
    order_id (int): ID of the order to update.
    Expected Body (JSON):
    status (str): New status. Accepted values:
    'Pending', 'In working', 'Done'.
    Returns:
    200 + Updated order JSON.
    400 + error if invalid status.
    404 + error if order not found.
    """
    data = request.get_json()
    if not data:
        return jsonify({'erro': 'Missing or invalid request body.'}), 400
    
    # Validate the status field
    valid_statuses = ['Pending', 'In working', 'Done']
    new_status = data.get('status', '').strip()
    
    if not new_status:
        return jsonify({'erro': 'Field "status" is required.'}), 400

    if new_status not in valid_statuses:
        return jsonify({ 'erro': f'Invalid status. Allowed values: {valid_statuses}' }), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if the order exists before trying to update
    cursor.execute('SELECT id FROM ordens WHERE id = ?', (order_id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({'erro': f'Order {order_id} not found.'}), 404
    
    # Execute the update
    cursor.execute('UPDATE ordens SET status = ? WHERE id = ?', (new_status, order_id))
    conn.commit()
    conn.close()
    
    # Return the updated record
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ordens WHERE id = ?', (order_id,))
    updated_order = cursor.fetchone()
    conn.close()
    
    return jsonify(dict(updated_order)), 200


# ── ROUTE 7: Remove an order (DELETE) ───────────────────────
@app.route('/ordens/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """
    Permanently removes a production order by ID.
    URL Parameters:
    order_id (int): ID of the order to be removed.
    Returns:
    200 + confirmation message.
    404 + error if order is not found.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verify existence BEFORE deleting
    cursor.execute('SELECT id, produto FROM ordens WHERE id = ?', (order_id,))
    order = cursor.fetchone()
    
    if order is None:
        conn.close()
        return jsonify({'erro': f'Order {order_id} not found.'}), 404
    
    # Save the product name to use in the confirmation message
    product_name = order['produto']
    
    # Execute removal
    cursor.execute('DELETE FROM ordens WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()
    
    return jsonify({ 
        'mensagem': f'Order {order_id} ({product_name}) removed successfully.', 
        'id_removido': order_id 
    }), 200


# ── ROUTE 8: Route with dynamic parameter ─────────────────
@app.route('/fabrica/<factory_name>')
def welcome_factory(factory_name):
    """
    Route with a dynamic parameter.
    The <factory_name> in the URL becomes a function argument.
    Example: GET /fabrica/WEG returns a customized message.
    """
    return jsonify({
        "mensagem": f"Welcome, {factory_name}! Online PO System.",
        "dica": "This is a Flask dynamic parameter route."
    })


# ── Start ───────────────────────────────────────────────
if __name__ == '__main__':
    # Boot DB before server   
    init_db()
    # debug=True restarts the server automatically when files are saved
    # host='0.0.0.0' allows access from other devices on the same network
    app.run(debug=True, host='0.0.0.0', port=5000)