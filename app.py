# ============================================================
# app.py – Back-end Flask of production orders system
# SENAI Jaraguá do Sul – Técnico em Cibersistemas para Automação
# ============================================================

import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from database import init_db, get_connection

# Create an instance of Flask application
# __name__ tell to Flask where to search resourses (templates, static, etc.)
app = Flask(__name__, static_folder='static', static_url_path='')

# enable CORS – let the front-end make requests to API without blocks of browser
CORS(app)

# ── ROUTE 1: Main page ──────────────────────────────────
@app.route('/')
def index():
    """Serve o arquivo index.html da pasta static."""
    return app.send_static_file('index.html')


# ── ROUTE 2: API stats ──────────────────────────────────
@app.route('/status')
def status():
    """Rota de health check com informacoes detalhadas."""
    # Conta quantas ordens existem no banco
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM ordens')
    resultado = cursor.fetchone()
    conn.close()
    
    return jsonify({
        "status": "online",
        "sistema": "Sistema de Ordens de Producao",
        "versao": "1.0.0",
        "total_ordens": resultado["total"],
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


# ── ROUTE 3: List all the orders (GET) ───────────────────
@app.route('/ordens', methods=['GET'])
def listar_ordens():
    # request.args acessa os parametros da query string
    # Ex: /ordens?status=Pendente → status_filtro = 'Pendente'
    status_filtro = request.args.get('status')
    conn = get_connection()
    cursor = conn.cursor()
    if status_filtro:
        cursor.execute('SELECT * FROM ordens WHERE status = ? ORDER BY id DESC', (status_filtro,) )
    else:
        cursor.execute('SELECT * FROM ordens ORDER BY id DESC')
    ordens = cursor.fetchall()
    conn.close()
    return jsonify([dict(o) for o in ordens])


# ── ROUTE 4: Buscar uma ordem específica pelo ID (GET) ───
@app.route('/ordens/<int:ordem_id>', methods=['GET'])
def buscar_ordem(ordem_id):
    """
    Busca uma unica ordem de producao pelo seu ID.
    Parametros de URL:
    ordem_id (int): ID da ordem a ser buscada.
    Retorna:
    200 + JSON da ordem, se encontrada.
    404 + mensagem de erro, se nao existir.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # O '?' e substituido pelo valor de ordem_id de forma segura
    cursor.execute('SELECT * FROM ordens WHERE id = ?', (ordem_id,))
    ordem = cursor.fetchone() # fetchone() retorna um unico registro ou None
    conn.close()
    
    # Se o ID nao existir, retornamos 404
    if ordem is None:
        return jsonify({'erro': f'Ordem {ordem_id} nao encontrada.'}), 404

    return jsonify(dict(ordem)), 200


# ── ROUTE 5: Criar nova ordem de producao (POST) ─────────
@app.route('/ordens', methods=['POST'])
def criar_ordem():
    """
    Cria uma nova ordem de producao a partir dos dados JSON enviados.
    Body esperado (JSON):
    produto (str): Nome do produto. Obrigatorio.
    quantidade (int): Quantidade de pecas. Obrigatorio, > 0.
    status (str): Opcional. Padrao: 'Pendente'.
    Retorna:
    201 + JSON da ordem criada, em caso de sucesso.
    400 + mensagem de erro, se dados invalidos.
    """
    dados = request.get_json()
    
    # ── Validacoes de entrada ───────────────────────────────
    # Verifica se o body foi enviado e é um JSON valido
    if not dados:
        return jsonify({'erro': 'Body da requisicao ausente ou invalido.'}), 400
    
    # Verifica campo obrigatorio 'produto'
    produto = dados.get('produto', '').strip()
    if not produto:
        return jsonify({'erro': 'Campo "produto" e obrigatorio e nao pode ser vazio.'}), 400
    
    # Verifica campo obrigatorio 'quantidade'
    quantidade = dados.get('quantidade')
    if quantidade is None:
        return jsonify({'erro': 'Campo "quantidade" e obrigatorio.'}), 400
    
    # Verifica se quantidade e um numero inteiro positivo
    try:
        quantidade = int(quantidade)
        if quantidade <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'erro': 'Campo "quantidade" deve ser um numero inteiro positivo.'}), 400
    
    # Status e opcional; usa 'Pendente' se nao informado
    status_validos = ['Pendente', 'Em andamento', 'Concluida']
    status = dados.get('status', 'Pendente')
    if status not in status_validos:
        return jsonify({'erro': f'Status invalido. Use: {status_validos}'}), 400

    # ── Insercao no banco ───────────────────────────────────
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO ordens (produto, quantidade, status) VALUES (?, ?, ?)',
        (produto, quantidade, status)
    )
    conn.commit()
    
    # Recuperamos o ID gerado automaticamente pelo banco
    novo_id = cursor.lastrowid
    conn.close()
    
    # Buscamos o registro recem-criado para retornar completo
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ordens WHERE id = ?', (novo_id,))
    nova_ordem = cursor.fetchone()
    conn.close()

    # Retorna 201 Created com o registro completo
    return jsonify(dict(nova_ordem)), 201

# ── ROTA: Atualizar status de uma ordem (PUT) ───────────────
@app.route('/ordens/<int:ordem_id>', methods=['PUT'])
def atualizar_ordem(ordem_id):
    """
    Atualiza o status de uma ordem de producao existente.
    Parametros de URL:
    ordem_id (int): ID da ordem a atualizar.
    Body esperado (JSON):
    status (str): Novo status. Valores aceitos:
    'Pendente', 'Em andamento', 'Concluida'.
    Retorna:
    200 + JSON da ordem atualizada.
    400 + erro se status invalido.
    404 + erro se ordem nao encontrada.
    """
 
    dados = request.get_json()
    if not dados:
        return jsonify({'erro': 'Body da requisicao ausente ou invalido.'}), 400
    
    # Valida o campo status
    status_validos = ['Pendente', 'Em andamento', 'Concluida']
    novo_status = dados.get('status', '').strip()
    
    if not novo_status:
        return jsonify({'erro': 'Campo "status" e obrigatorio.'}), 400

    if novo_status not in status_validos:
        return jsonify({ 'erro': f'Status invalido. Valores permitidos: {status_validos}' }), 400
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verifica se a ordem existe antes de tentar atualizar
    cursor.execute('SELECT id FROM ordens WHERE id = ?', (ordem_id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({'erro': f'Ordem {ordem_id} nao encontrada.'}), 404
    
    # Executa a atualizacao
    cursor.execute( 'UPDATE ordens SET status = ? WHERE id = ?', (novo_status, ordem_id))
    conn.commit()
    conn.close()
    
    # Retorna o registro atualizado
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ordens WHERE id = ?', (ordem_id,))
    ordem_atualizada = cursor.fetchone()
    conn.close()
    return jsonify(dict(ordem_atualizada)), 200

# ── ROTA: Remover uma ordem (DELETE) ───────────────────────
@app.route('/ordens/<int:ordem_id>', methods=['DELETE'])
def remover_ordem(ordem_id):
    """
    Remove permanentemente uma ordem de producao pelo ID.
    Parametros de URL:
    ordem_id (int): ID da ordem a ser removida.
    Retorna:
    200 + mensagem de confirmacao.
    404 + erro se a ordem nao for encontrada.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verifica existencia ANTES de deletar
    cursor.execute('SELECT id, produto FROM ordens WHERE id = ?', (ordem_id,))
    ordem = cursor.fetchone()
    if ordem is None:
        conn.close()
        return jsonify({'erro': f'Ordem {ordem_id} nao encontrada.'}), 404
    
    # Guarda o nome do produto para usar na mensagem de confirmacao
    nome_produto = ordem['produto']
    
    # Executa a remocao
    cursor.execute('DELETE FROM ordens WHERE id = ?', (ordem_id,))
    conn.commit()
    conn.close()
    return jsonify({ 'mensagem': f'Ordem {ordem_id} ({nome_produto}) removida com sucesso.', 'id_removido': ordem_id }), 200


# ── ROUTE 6: Rota com parametro dinamico ─────────────────
@app.route('/fabrica/<nome_fabrica>')
def boas_vindas(nome_fabrica):
    """
    Rota com parametro dinamico.
    O <nome_fabrica> na URL vira um argumento da funcao.
    Exemplo: GET /fabrica/WEG retorna mensagem personalizada.
    """
    return jsonify({
        "mensagem": f"Bem-vindo, {nome_fabrica}! Sistema de OP online.",
        "dica": "Esta e uma rota com parametro dinamico do Flask."
    })


# ── Start ───────────────────────────────────────────────
if __name__ == '__main__':
    # Boot DB before server   
    init_db()
    # debug=True restart the server automatically when the files are saved
    # host='0.0.0.0' let the acess to another devices at the same network
    app.run(debug=True, host='0.0.0.0', port=5000)