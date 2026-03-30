// URLs da nossa API Flask
const API_URL_STATUS = 'http://localhost:5000/status';
const API_URL_ORDENS = 'http://localhost:5000/ordens';

// Elementos do DOM
const statusDot = document.getElementById('connection-dot');
const statusText = document.getElementById('connection-text');
const totalOrdensEl = document.getElementById('total-ordens');
const serverTimeEl = document.getElementById('server-time');
const tableBody = document.getElementById('ordens-body');

// Função para checar a saúde do servidor
async function fetchStatus() {
    try {
        const response = await fetch(API_URL_STATUS);
        const data = await response.json();

        if (data.status === 'online') {
            statusDot.className = 'status-dot online';
            statusText.textContent = 'Sistema Online';
            totalOrdensEl.textContent = data.total_ordens;
            // Extrai apenas a hora da string de timestamp
            serverTimeEl.textContent = data.timestamp.split(' ')[1]; 
        }
    } catch (error) {
        console.error('Erro ao conectar com o servidor:', error);
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'Servidor Offline';
        totalOrdensEl.textContent = 'Erro';
    }
}

// Função para buscar e renderizar as ordens
async function fetchOrdens() {
    try {
        const response = await fetch(API_URL_ORDENS);
        const ordens = await response.json();

        // Limpa a tabela antes de inserir novos dados
        tableBody.innerHTML = '';

        if (ordens.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Nenhuma ordem encontrada.</td></tr>';
            return;
        }

        ordens.forEach(ordem => {
            const tr = document.createElement('tr');
            
            // Define a classe da badge baseado no status (para futuras cores)
            const statusClass = ordem.status.toLowerCase();

            tr.innerHTML = `
                <td>#${ordem.id}</td>
                <td><strong>${ordem.produto}</strong></td>
                <td>${ordem.quantidade} un.</td>
                <td><span class="status-badge ${statusClass}">${ordem.status}</span></td>
                <td>${ordem.criado_em}</td>
            `;
            tableBody.appendChild(tr);
        });

    } catch (error) {
        console.error('Erro ao buscar ordens:', error);
        tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:red;">Erro ao carregar dados.</td></tr>';
    }
}

// Inicialização: Chama as funções assim que a página carrega
document.addEventListener('DOMContentLoaded', () => {
    fetchStatus();
    fetchOrdens();
    
    // Atualiza o status do servidor a cada 30 segundos
    setInterval(fetchStatus, 30000);
});