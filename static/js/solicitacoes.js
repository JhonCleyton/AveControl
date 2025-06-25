// Carregar solicitações ao carregar a página
document.addEventListener('DOMContentLoaded', function() {
    carregarSolicitacoesExclusao();
});

// Função para carregar solicitações de exclusão
function carregarSolicitacoesExclusao() {
    const container = document.getElementById('lista-solicitacoes-exclusao');
    if (!container) return;

    fetch('/api/documentos/solicitacoes-exclusao')
    .then(response => response.json())
    .then(data => {
        if (data.solicitacoes.length === 0) {
            container.innerHTML = '<div class="alert alert-info">Não há solicitações de exclusão pendentes.</div>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'table table-hover';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Carga</th>
                    <th>Documento</th>
                    <th>Solicitante</th>
                    <th>Data</th>
                    <th>Motivo</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody></tbody>
        `;

        const tbody = table.querySelector('tbody');
        data.solicitacoes.forEach(sol => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <a href="/cargas/${sol.carga_id}" target="_blank">
                        ${sol.numero_carga}
                    </a>
                </td>
                <td>${sol.tipo_documento}</td>
                <td>${sol.solicitado_por_nome}</td>
                <td>${new Date(sol.data_solicitacao).toLocaleString()}</td>
                <td>${sol.motivo}</td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-success btn-sm" onclick="processarSolicitacao(${sol.documento_id}, true, '${sol.tipo_documento}')">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="processarSolicitacao(${sol.documento_id}, false, '${sol.tipo_documento}')">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });

        container.innerHTML = '';
        container.appendChild(table);
    })
    .catch(error => {
        console.error('Erro ao carregar solicitações:', error);
        container.innerHTML = '<div class="alert alert-danger">Erro ao carregar solicitações.</div>';
    });
}

// Função para processar solicitação (aprovar/rejeitar)
function processarSolicitacao(docId, aprovar, tipoDoc) {
    const modal = new bootstrap.Modal(document.getElementById('modalConfirmacao'));
    const mensagem = document.getElementById('mensagem-confirmacao');
    const btnConfirmar = document.getElementById('btnConfirmarAcao');
    const observacaoInput = document.getElementById('observacao');

    mensagem.textContent = `Deseja ${aprovar ? 'aprovar' : 'rejeitar'} a exclusão do documento "${tipoDoc}"?`;
    observacaoInput.value = '';

    // Remover handler anterior se existir
    btnConfirmar.onclick = null;

    // Adicionar novo handler
    btnConfirmar.onclick = function() {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        fetch(`/api/documentos/${docId}/aprovar-exclusao`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                aprovado: aprovar,
                observacao: observacaoInput.value
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(json => {
                    throw new Error(json.error || 'Erro ao processar solicitação');
                });
            }
            return response.json();
        })
        .then(data => {
            modal.hide();
            Swal.fire({
                icon: 'success',
                title: 'Sucesso',
                text: `Solicitação ${aprovar ? 'aprovada' : 'rejeitada'} com sucesso`,
                timer: 2000,
                showConfirmButton: false
            });
            carregarSolicitacoesExclusao();
        })
        .catch(error => {
            console.error('Erro ao processar solicitação:', error);
            Swal.fire({
                icon: 'error',
                title: 'Erro',
                text: error.message || 'Erro ao processar solicitação'
            });
        });
    };

    modal.show();
}
