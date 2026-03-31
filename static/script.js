const API_URL = 'http://localhost:5000';

// Elementos
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const serverTime = document.getElementById('server-time');
const totalOrdens = document.getElementById('total-ordens');
const gridOrdens = document.getElementById('grid-ordens');
const formOrdem = document.getElementById('form-ordem');

// 1. Verifica a saúde da API e atualiza o estado
async function checkStatus() {
    try {
        const res = await fetch(`${API_URL}/status`);
        const data = await res.json();
        
        statusIndicator.className = 'indicator online';
        statusText.textContent = 'Sistema Online';
        serverTime.textContent = `| Atualizado às: ${data.timestamp.split(' ')[1]}`;
        totalOrdens.textContent = data.total_ordens;
    } catch (err) {
        statusIndicator.className = 'indicator offline';
        statusText.textContent = 'Servidor Offline';
        serverTime.textContent = '';
    }
}

// 2. Busca e renderiza as Ordens de Produção
async function loadOrdens() {
    try {
        const res = await fetch(`${API_URL}/ordens`);
        const ordens = await res.json();
        
        gridOrdens.innerHTML = '';
        
        if (ordens.length === 0) {
            gridOrdens.innerHTML = '<p style="color: #6b7280; grid-column: 1/-1;">Nenhuma ordem de produção encontrada.</p>';
            return;
        }

        ordens.forEach(ordem => {
            // Define a classe da cor baseada no estado
            const statusClass = ordem.status.toLowerCase().replace(' ', '-');
            
            const card = document.createElement('div');
            card.className = 'ordem-card';
            
            // Lógica para mostrar os botões corretos com base no estado
            let botoesHTML = '';
            
            if (ordem.status === 'Pendente') {
                botoesHTML += `
                    <button class="btn-action btn-iniciar" onclick="iniciarOrdem(${ordem.id})">
                        <span class="material-icons" style="font-size: 16px;">play_arrow</span> Iniciar
                    </button>
                `;
            }
            
            if (ordem.status !== 'Concluida') {
                botoesHTML += `
                    <button class="btn-action btn-concluir" onclick="concluirOrdem(${ordem.id})">
                        <span class="material-icons" style="font-size: 16px;">check</span> Concluir
                    </button>
                `;
            }
            
            botoesHTML += `
                <button class="btn-action btn-deletar" onclick="deletarOrdem(${ordem.id})">
                    <span class="material-icons" style="font-size: 16px;">delete</span> Excluir
                </button>
            `;

            card.innerHTML = `
                <div class="ordem-header">
                    <div>
                        <span class="ordem-id">OP #${ordem.id}</span>
                        <div class="ordem-produto">${ordem.produto}</div>
                        <div class="ordem-qtd">Qtd: ${ordem.quantidade} un.</div>
                    </div>
                    <span class="badge ${statusClass}">${ordem.status}</span>
                </div>
                
                <div class="ordem-actions">
                    ${botoesHTML}
                </div>
            `;
            gridOrdens.appendChild(card);
        });
    } catch (err) {
        console.error('Erro ao carregar ordens:', err);
    }
}

// 3. Criar uma nova Ordem (POST)
formOrdem.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const produto = document.getElementById('produto').value;
    const quantidade = document.getElementById('quantidade').value;

    try {
        await fetch(`${API_URL}/ordens`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ produto, quantidade: parseInt(quantidade) })
        });
        
        formOrdem.reset();
        refreshData(); // Atualiza o ecrã
    } catch (err) {
        alert('Erro ao criar ordem!');
    }
});

// 4. Atualizar Estado para "Em andamento" (PUT)
async function iniciarOrdem(id) {
    try {
        await fetch(`${API_URL}/ordens/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'Em andamento' })
        });
        refreshData();
    } catch (err) {
        alert('Erro ao iniciar ordem!');
    }
}

// 5. Atualizar Estado para "Concluida" (PUT)
async function concluirOrdem(id) {
    try {
        await fetch(`${API_URL}/ordens/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'Concluida' })
        });
        refreshData();
    } catch (err) {
        alert('Erro ao concluir ordem!');
    }
}

// 6. Eliminar Ordem (DELETE)
async function deletarOrdem(id) {
    if(!confirm(`Tem a certeza que deseja eliminar a OP #${id}?`)) return;

    try {
        await fetch(`${API_URL}/ordens/${id}`, {
            method: 'DELETE'
        });
        refreshData();
    } catch (err) {
        alert('Erro ao eliminar ordem!');
    }
}

// Função auxiliar para atualizar todos os dados
function refreshData() {
    checkStatus();
    loadOrdens();
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    refreshData();
    setInterval(refreshData, 10000); // Atualiza dados a cada 10 segundos
});