# ============================================================
# app.py – Back-end Flask of production orders system
# SENAI Jaraguá do Sul – Técnico em Cibersistemas para Automação
# ============================================================

import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from database import init_db, get_connection
from functools import wraps
import html


# Create an instance of Flask application
# __name__ tells Flask where to search resources (templates, static, etc.)
app = Flask(__name__, static_folder='static', static_url_path='')

# Enable CORS – allows the front-end to make requests to the API without browser blocks
CORS(app)

# ── Security configuration ────────────────────────────
API_KEY = 'senai-cibersistemas-2026-chave-segura'


def requer_autenticacao(f):
    """
    Decorator que protege rotas exigindo API Key valida.
    O cliente deve enviar o cabecalho:
    X-API-Key: <valor da API_KEY configurada>
    Se a chave estiver ausente ou incorreta, retorna 401 Unauthorized.
    Se correta, executa a funcao de rota normalmente.
    Uso:
    @app.route('/rota')
    @requer_autenticacao
    def minha_rota():
    ...
    """
    @wraps(f) # Preserva o nome e docstring da funcao original
    def decorator(*args, **kwargs):
        # Lê o cabeçalho X-API-Key da requisição
        received_key = request.headers.get('X-API-Key')
        
        if not received_key:
            return jsonify({
            'error': 'Authentication needed.',
            'instruction': 'Send the Header X-API-Key with your own key.'
            }), 401
        if received_key != API_KEY:
            return jsonify({
            'erro': 'Invalid API key.'
            }), 403
            
        # Right key: rote fuction will be executed normally
        return f(*args, **kwargs)
    return decorator




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
    """
    List all the production orders ordening by ID DESC
    
    Public route – nao requer autenticacao.

    Methods:
        GET /ordens
        GET /ordens?status=Pendente (filtro opcional por status)
        
        Args:
            status (str, query param, opcional): Filtra ordens por status.
                Valores aceitos: 'Pendente', 'Em andamento', 'Concluida'.

        Returns:
            Response: JSON com lista de ordens. Status HTTP 200.
            Retorna lista vazia [] se nenhuma ordem existir.

        Example:
            GET /ordens → 200 [{id:1, produto:..., status:'Pendente'}, ...]
            GET /ordens?status=Pendente → 200 [ordens apenas pendentes]
                """
    
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
@requer_autenticacao
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
    
    # Limite de tamanho: evita strings absurdamente longas
    if len(product_val) > 200:
        return jsonify({'erro': 'Nome do produto muito longo (max 200 caracteres).'}), 400

    
    # Check required field 'quantidade'
    quantity_val = data.get('quantidade')
    if quantity_val is None:
        return jsonify({'erro': 'Field "quantidade" is required.'}), 400
    
    # Check if quantity is a positive integer
    try:
        quantity_val = int(quantity_val)
        if quantity_val <= 0 or quantity_val > 999999:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'erro': 'Field "quantidade" must be a positive integer and between 1 and 999999.'}), 400
    
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
@requer_autenticacao
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
@requer_autenticacao
def delete_order(order_id):
    """
    Remove permanentemente uma ordem de producao.

    Rota protegida – requer cabecalho X-API-Key valido.

    Methods:
        DELETE /ordens/<id>
        
    Args:
        ordem_id (int): ID da ordem a ser removida (via URL).
        
    Returns:
        Response: JSON com mensagem de confirmacao. Status 200.
        Response: JSON com erro. Status 404 se ID nao existir.
        Response: JSON com erro. Status 401/403 se sem autenticacao.
        
    Example:
        DELETE /ordens/5 → 200 {mensagem: 'Ordem 5 (Motor...) removida.'}
        DELETE /ordens/999 → 404 {erro: 'Ordem 999 nao encontrada.'}
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



@app.errorhandler(400)
def requisicao_invalida(erro):
    """Returns JSON para erros de requisição mal formada."""
    return jsonify({'erro': 'Requisicao invalida.', 'detalhe': str(erro)}), 400

@app.errorhandler(401)
def nao_autorizado(erro):
    """Retorna JSON para erros de autenticação."""
    return jsonify({'erro': 'Autenticacao necessaria.'}), 401

@app.errorhandler(403)
def acesso_negado(erro):
    """Retorna JSON para erros de autorização."""
    return jsonify({'erro': 'Acesso negado.'}), 403


@app.errorhandler(404)
def nao_encontrado(erro):
    """Retorna JSON para recursos não encontrados."""
    return jsonify({'erro': 'Recurso nao encontrado.'}), 404

@app.errorhandler(405)
def metodo_nao_permitido(erro):
    """Retorna JSON quando o método HTTP não é suportado pela rota."""
    return jsonify({'erro': 'Metodo HTTP nao permitido nesta rota.'}), 405


@app.errorhandler(500)
def erro_interno(erro):
    """Retorna JSON genérico para erros internos sem expor detalhes."""
    # NUNCA retorne str(erro) aqui em producao – expõe stack trace
    return jsonify({'erro': 'Erro interno do servidor. Contate o administrador.'}), 500


# ── Start ───────────────────────────────────────────────
if __name__ == '__main__':
    # Boot DB before server   
    init_db()
    # debug=True restarts the server automatically when files are saved
    # host='0.0.0.0' allows access from other devices on the same network
    app.run(debug=True, host='0.0.0.0', port=5000)