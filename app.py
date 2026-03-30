# ============================================================
# app.py – Back-end Flask of production orders system
# SENAI Jaraguá do Sul – Técnico em Cibersistemas para Automação
# ============================================================

from flask import Flask, jsonify, request
from flask_cors import CORS
from database import init_db, get_connection
import datetime

# Create an instance of Flask application
# __name__ tell to Flask where to search resourses (tamplates, static, etc.)
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
 
# ── ROUTER 3: List all the orders (GET) ───────────────────
@app.route('/ordens', methods=['GET'])
def listar_ordens():
 """
 Lista todas as ordens de producao cadastradas.
 Metodo HTTP: GET
 URL: http://localhost:5000/ordens
 Retorna: Lista de ordens em formato JSON.
 """
 conn = get_connection()
 cursor = conn.cursor()
 cursor.execute('SELECT * FROM ordens ORDER BY id DESC')
 ordens = cursor.fetchall()
 conn.close()
 # Convert each Row of SQLite in python dictionary to 
 # Converte cada Row do SQLite em dicionário Python para serialize in JSON
 return jsonify([dict(o) for o in ordens])

# ── ROTA DE TESTE: Inserir dado falso (GET) ───────────────────
@app.route('/gerar-teste')
def gerar_teste():
    """
    Rota temporária apenas para testar a inserção no banco de dados.
    """
    # 1. Abre a conexão com o banco
    conn = get_connection()
    cursor = conn.cursor()
    
    # 2. Executa o comando SQL para inserir um dado fixo
    cursor.execute('''
        INSERT INTO ordens (produto, quantidade, status) 
        VALUES ('Motor WEG W22 - Teste', 15, 'Em Produção')
    ''')
    
    # 3. Salva (commit) e fecha a conexão
    conn.commit()
    conn.close()
    
    return jsonify({"mensagem": "Ordem de teste criada com sucesso! Vá para /ordens para ver."})


@app.route('/fabrica/<nome_fabrica>')
def boas_vindas(nome_fabrica):
 """
 Rota com parametro dinamico.
 O <nome_fabrica> na URL vira um argumento da funcao.
 Exemplo: GET /fabrica/WEG retorna mensagem personalizada.
 """
 return jsonify({
 "mensagem": f"Bem-vindo, {nome_fabrica}! Sistema de OP online.",
 "dica": "Esta e uma rota com parametro dinamico do Flask."})



# ── Start ───────────────────────────────────────
if __name__ == '__main__':
 # Boot DB before server   
 init_db()
 # debug=True restart the server automatically when the files are saved
 # host='0.0.0.0' let the acess to another devices at the same network
 app.run(debug=True, host='0.0.0.0', port=5000)
