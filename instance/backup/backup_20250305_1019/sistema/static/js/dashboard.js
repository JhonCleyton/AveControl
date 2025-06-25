let statusChart = null;

function atualizarDashboard() {
    const btnAtualizar = document.getElementById('atualizar-dashboard');
    if (btnAtualizar) {
        btnAtualizar.disabled = true;
        btnAtualizar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Atualizando...';
    }

    fetch('/api/dashboard/stats')
        .then(response => response.json())
        .then(stats => {
            // Atualizar contadores
            document.querySelector('[data-stat="total_cargas"]').textContent = stats.total_cargas;
            document.querySelector('[data-stat="cargas_pendentes"]').textContent = stats.cargas_pendentes;
            document.querySelector('[data-stat="cargas_hoje"]').textContent = stats.cargas_hoje;
            document.querySelector('[data-stat="cargas_mes"]').textContent = stats.cargas_mes;
            document.getElementById('usuarios-online').textContent = stats.usuarios_online;
            
            // Atualizar gráfico
            if (statusChart) {
                statusChart.data.datasets[0].data = [
                    stats.stats_status.pendente,
                    stats.stats_status.em_andamento,
                    stats.stats_status.concluida,
                    stats.stats_status.cancelada
                ];
                statusChart.update('none');
            }
            
            // Atualizar lista de últimas cargas
            const ultimasCargasContainer = document.getElementById('ultimas-cargas');
            if (ultimasCargasContainer) {
                ultimasCargasContainer.innerHTML = stats.ultimas_cargas.length ? 
                    stats.ultimas_cargas.map(carga => `
                        <div class="list-group-item">
                            <div class="d-flex w-100 justify-content-between">
                                <h6 class="mb-1">${carga.numero_carga}</h6>
                                <small class="text-muted">${carga.criado_em}</small>
                            </div>
                            <small class="text-muted">Status: ${carga.status}</small>
                        </div>
                    `).join('') :
                    '<div class="list-group-item"><p class="mb-1">Nenhuma carga registrada</p></div>';
            }
            
            // Atualizar lista de notificações
            const notificacoesContainer = document.getElementById('notificacoes');
            if (notificacoesContainer) {
                notificacoesContainer.innerHTML = stats.notificacoes.length ?
                    stats.notificacoes.map(notif => `
                        <div class="list-group-item">
                            <div class="d-flex w-100 justify-content-between">
                                <p class="mb-1">${notif.mensagem}</p>
                                <small class="text-muted">${notif.criado_em}</small>
                            </div>
                        </div>
                    `).join('') :
                    '<div class="list-group-item"><p class="mb-1">Nenhuma notificação pendente</p></div>';
            }
        })
        .catch(error => console.error('Erro ao atualizar dashboard:', error))
        .finally(() => {
            if (btnAtualizar) {
                btnAtualizar.disabled = false;
                btnAtualizar.innerHTML = '<i class="fas fa-sync-alt"></i> Atualizar';
            }
        });
}

function inicializarDashboard(statusData) {
    const ctx = document.getElementById('statusChart').getContext('2d');
    
    if (statusChart) {
        statusChart.destroy();
    }
    
    statusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Pendente', 'Em Andamento', 'Concluída', 'Cancelada'],
            datasets: [{
                data: [
                    statusData.pendente,
                    statusData.em_andamento,
                    statusData.concluida,
                    statusData.cancelada
                ],
                backgroundColor: [
                    '#ffc107',  // Amarelo para pendente
                    '#17a2b8',  // Azul para em andamento
                    '#28a745',  // Verde para concluída
                    '#dc3545'   // Vermelho para cancelada
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
    
    const btnAtualizar = document.getElementById('atualizar-dashboard');
    if (btnAtualizar) {
        btnAtualizar.addEventListener('click', atualizarDashboard);
    }
}

window.addEventListener('beforeunload', function() {
    if (statusChart) {
        statusChart.destroy();
    }
});
