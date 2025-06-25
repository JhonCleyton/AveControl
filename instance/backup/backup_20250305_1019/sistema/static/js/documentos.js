// Módulo de documentos usando um padrão que evita redeclarações
window.DocumentosModule = window.DocumentosModule || (function() {
    // Variáveis privadas do módulo
    let uploadInProgress = false;
    let documentosInitialized = false;

    // Função para formatar data
    function formatarData(dataStr) {
        if (!dataStr) return 'Data não disponível';
        try {
            // Garantir que a data tem o 'Z' para indicar UTC
            if (!dataStr.endsWith('Z') && !dataStr.includes('+')) {
                dataStr += 'Z';
            }
            const data = new Date(dataStr);
            if (isNaN(data.getTime())) {
                console.error('Data inválida:', dataStr);
                return 'Data não disponível';
            }
            
            // Ajustar para o timezone local
            const options = {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false,
                timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
            };
            
            return new Intl.DateTimeFormat('pt-BR', options).format(data);
        } catch (e) {
            console.error('Erro ao formatar data:', e);
            return 'Data não disponível';
        }
    }

    // Função para confirmar exclusão
    function confirmarExclusao(docId) {
        if (!docId) {
            console.error('ID do documento não fornecido');
            return;
        }

        // Atualizar o ID do documento no modal
        document.getElementById('documentoIdExclusao').value = docId;

        // Exibir o modal de exclusão
        const modalElement = document.getElementById('modalSolicitarExclusao');
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }

    // Função para listar documentos de uma carga
    function listarDocumentos(cargaId) {
        if (!cargaId) {
            // Se não houver ID, apenas limpar a lista
            const listaDocumentos = document.getElementById('lista-documentos');
            if (listaDocumentos) {
                listaDocumentos.innerHTML = '<div class="alert alert-info">Nenhum documento disponível.</div>';
            }
            return;
        }
        
        console.log('Listando documentos para carga:', cargaId);
        fetch(`/api/carga/${cargaId}/documentos`)
        .then(response => response.json())
        .then(data => {
            console.log('Dados recebidos do servidor:', data);
            const listaDocumentos = document.getElementById('lista-documentos');
            if (!listaDocumentos) return;
            
            listaDocumentos.innerHTML = '';

            // Verificar se há documentos na resposta
            const documentos = data || [];
            if (documentos.length === 0) {
                listaDocumentos.innerHTML = '<div class="alert alert-info">Nenhum documento encontrado.</div>';
                return;
            }

            // Criar tabela de documentos
            const table = document.createElement('table');
            table.className = 'table table-striped table-hover';
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>Tipo</th>
                        <th>Status</th>
                        <th>Data</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody></tbody>
            `;

            const tbody = table.querySelector('tbody');
            
            // Usar Set para rastrear documentos únicos pelo ID
            const processedIds = new Set();
            
            documentos.forEach(doc => {
                if (processedIds.has(doc.id)) return;
                processedIds.add(doc.id);
                
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${doc.tipo_documento}${doc.outro_tipo_descricao ? ` - ${doc.outro_tipo_descricao}` : ''}</td>
                    <td>
                        ${doc.ausente ? 
                            `<span class="badge bg-danger">Ausente</span>
                             <div class="small text-muted mt-1">Motivo: ${doc.motivo_ausencia}</div>` : 
                         doc.status_exclusao === 'pendente' ? '<span class="badge bg-warning text-dark">Exclusão Pendente</span>' :
                         '<span class="badge bg-success">Presente</span>'}
                    </td>
                    <td>${formatarData(doc.data_upload)}</td>
                    <td>
                        ${!doc.ausente ? `
                            <button class="btn btn-sm btn-info me-1" onclick="DocumentosModule.visualizarDocumento(${doc.id})" title="Visualizar">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-primary me-1" onclick="DocumentosModule.downloadDocumento(${doc.id})" title="Download">
                                <i class="fas fa-download"></i>
                            </button>
                        ` : ''}
                        ${doc.status_exclusao !== 'pendente' ? `
                            <button class="btn btn-sm btn-danger" onclick="DocumentosModule.confirmarExclusao(${doc.id})" title="Excluir">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                    </td>
                `;
                tbody.appendChild(tr);
            });

            listaDocumentos.appendChild(table);
        })
        .catch(error => {
            console.error('Erro ao listar documentos:', error);
            const listaDocumentos = document.getElementById('lista-documentos');
            if (listaDocumentos) {
                listaDocumentos.innerHTML = '<div class="alert alert-danger">Erro ao carregar documentos. Por favor, tente novamente.</div>';
            }
        });
    }

    // Função para download de documento
    function downloadDocumento(docId) {
        const link = document.createElement('a');
        link.href = `/api/documentos/${docId}/download`;
        link.download = ''; // Isso força o download em vez de abrir no navegador
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Função para visualizar documento
    function visualizarDocumento(docId) {
        const url = `/api/documentos/${docId}/visualizar`;
        window.open(url, '_blank');
    }

    // Função para adicionar novo documento
    function adicionarDocumento(cargaId, formData) {
        if (uploadInProgress) {
            console.log('Upload já em andamento, aguarde...');
            return Promise.reject(new Error('Upload já em andamento, aguarde...'));
        }

        console.log('Adicionando documento para carga:', cargaId);
        
        // Criar novo FormData para garantir dados corretos
        const newFormData = new FormData();
        
        // Adicionar tipo do documento
        const tipoDocumento = formData.get('tipo_documento');
        if (!tipoDocumento) {
            throw new Error('Selecione o tipo de documento');
        }
        newFormData.append('tipo_documento', tipoDocumento);

        // Adicionar descrição se for outro tipo
        if (tipoDocumento === 'Outro') {
            const outroTipoDescricao = formData.get('outro_tipo_descricao');
            if (!outroTipoDescricao) {
                throw new Error('Especifique o tipo de documento');
            }
            newFormData.append('outro_tipo_descricao', outroTipoDescricao);
        }

        // Tratar ausência
        const ausente = formData.get('ausente') === 'on';
        newFormData.append('ausente', ausente ? 'true' : 'false');

        if (ausente) {
            const motivoAusencia = formData.get('motivo_ausencia');
            if (!motivoAusencia) {
                throw new Error('Informe o motivo da ausência');
            }
            newFormData.append('motivo_ausencia', motivoAusencia);
        } else {
            const arquivo = formData.get('arquivo');
            if (!arquivo || arquivo.size === 0) {
                throw new Error('Selecione um arquivo para upload');
            }
            newFormData.append('arquivo', arquivo);
        }

        uploadInProgress = true;
        const submitButton = document.querySelector('#form-documento button[type="submit"]');
        if (submitButton) submitButton.disabled = true;

        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        return fetch(`/api/carga/${cargaId}/documentos`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: newFormData
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    try {
                        const data = JSON.parse(text);
                        throw new Error(data.error || 'Erro ao adicionar documento');
                    } catch (e) {
                        console.error('Resposta do servidor:', text);
                        throw new Error('Erro ao processar resposta do servidor');
                    }
                });
            }
            return response.json();
        })
        .then(result => {
            console.log('Documento adicionado com sucesso:', result);
            listarDocumentos(cargaId);
            return result;
        })
        .catch(error => {
            console.error('Erro completo:', error);
            throw error;
        })
        .finally(() => {
            uploadInProgress = false;
            if (submitButton) submitButton.disabled = false;
        });
    }

    // Função para solicitar exclusão de documento
    function solicitarExclusao(docId) {
        const motivo = document.getElementById('motivoExclusao').value.trim();
        if (!motivo) {
            Swal.fire('Erro', 'O motivo é obrigatório', 'error');
            return;
        }

        // Enviar solicitação
        fetch(`/api/documentos/${docId}/solicitar-exclusao`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({ motivo: motivo })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao solicitar exclusão');
            }
            return response.json();
        })
        .then(result => {
            if (result.message) {
                // Fechar o modal
                const modalElement = document.getElementById('modalSolicitarExclusao');
                const modal = bootstrap.Modal.getInstance(modalElement);
                modal.hide();

                // Limpar o campo de motivo
                document.getElementById('motivoExclusao').value = '';

                // Mostrar mensagem de sucesso
                Swal.fire('Sucesso', 'Solicitação de exclusão registrada', 'success');

                // Atualizar a lista de documentos
                const cargaId = document.querySelector('[data-carga-id]').dataset.cargaId;
                if (cargaId) {
                    listarDocumentos(cargaId);
                }
            } else {
                throw new Error(result.error || 'Erro ao solicitar exclusão');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            Swal.fire('Erro', error.message || 'Erro ao processar solicitação', 'error');
        });
    }

    // Função para aprovar/rejeitar exclusão
    function aprovarExclusao(docId, aprovado) {
        // Criar o modal dinamicamente
        const modalHtml = `
            <div class="modal fade" id="modalAprovarExclusao" tabindex="-1" aria-labelledby="modalAprovarExclusaoLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="modalAprovarExclusaoLabel">${aprovado ? 'Aprovar' : 'Rejeitar'} Exclusão</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="formAprovarExclusao">
                                <div class="mb-3">
                                    <label for="observacaoExclusao" class="form-label">
                                        ${aprovado ? 'Observação (opcional)' : 'Motivo da Rejeição'}
                                    </label>
                                    <textarea class="form-control" id="observacaoExclusao" rows="3" ${aprovado ? '' : 'required'}></textarea>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-primary" id="btnConfirmarAprovacao">Confirmar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remover modal anterior se existir
        const modalAnterior = document.getElementById('modalAprovarExclusao');
        if (modalAnterior) {
            modalAnterior.remove();
        }

        // Adicionar o novo modal ao documento
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Inicializar o modal do Bootstrap
        const modalElement = document.getElementById('modalAprovarExclusao');
        const modal = new bootstrap.Modal(modalElement);

        // Configurar o botão de confirmação
        const btnConfirmar = document.getElementById('btnConfirmarAprovacao');
        btnConfirmar.onclick = () => {
            const observacao = document.getElementById('observacaoExclusao').value.trim();
            if (!aprovado && !observacao) {
                alert('O motivo da rejeição é obrigatório');
                return;
            }

            fetch(`/api/documentos/${docId}/aprovar-exclusao`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({
                    aprovado: aprovado,
                    observacao: observacao
                })
            })
            .then(response => response.json())
            .then(result => {
                if (result.message) {
                    modal.hide();
                    Swal.fire('Sucesso', result.message, 'success').then(() => {
                        window.location.reload();
                    });
                } else {
                    throw new Error(result.error || 'Erro ao processar solicitação');
                }
            })
            .catch(error => {
                console.error('Erro:', error);
                Swal.fire('Erro', error.message || 'Erro ao processar solicitação', 'error');
            });
        };

        // Mostrar o modal
        modal.show();
    }

    // Função para inicializar o módulo de documentos
    function inicializarModulo() {
        if (documentosInitialized) {
            console.log('Módulo de documentos já inicializado');
            return;
        }

        console.log('Inicializando módulo de documentos');
        const cargaIdElement = document.querySelector('[data-carga-id]');
        if (cargaIdElement) {
            const cargaId = cargaIdElement.dataset.cargaId;
            console.log('ID da carga:', cargaId);
            listarDocumentos(cargaId);
        }

        const formDoc = document.getElementById('form-documento');
        if (formDoc) {
            const tipoSelect = formDoc.querySelector('[name="tipo_documento"]');
            const outroTipoDiv = formDoc.querySelector('#outro-tipo-div');
            const outroTipoInput = formDoc.querySelector('[name="outro_tipo_descricao"]');
            const ausenteCheck = formDoc.querySelector('[name="ausente"]');
            const uploadDiv = formDoc.querySelector('#upload-div');
            const uploadInput = formDoc.querySelector('[name="arquivo"]');
            const motivoAusenciaDiv = formDoc.querySelector('#motivo-ausencia-div');
            const motivoAusenciaInput = formDoc.querySelector('[name="motivo_ausencia"]');

            if (tipoSelect) {
                tipoSelect.addEventListener('change', () => {
                    const isOutro = tipoSelect.value === 'Outro';
                    outroTipoDiv.style.display = isOutro ? 'block' : 'none';
                    if (isOutro) {
                        outroTipoInput.required = true;
                        outroTipoInput.focus();
                    } else {
                        outroTipoInput.required = false;
                        outroTipoInput.value = '';
                    }
                });
            }

            if (ausenteCheck) {
                ausenteCheck.addEventListener('change', () => {
                    const isAusente = ausenteCheck.checked;
                    uploadDiv.style.display = isAusente ? 'none' : 'block';
                    motivoAusenciaDiv.style.display = isAusente ? 'block' : 'none';
                    if (isAusente) {
                        uploadInput.value = '';
                        uploadInput.required = false;
                        motivoAusenciaInput.required = true;
                        motivoAusenciaInput.focus();
                    } else {
                        motivoAusenciaInput.value = '';
                        motivoAusenciaInput.required = false;
                        uploadInput.required = true;
                    }
                });
            }

            formDoc.addEventListener('submit', (e) => {
                e.preventDefault();
                
                if (uploadInProgress) {
                    console.log('Upload já em andamento, aguarde...');
                    return;
                }

                const formData = new FormData(formDoc);
                const cargaId = document.querySelector('[data-carga-id]').dataset.cargaId;

                adicionarDocumento(cargaId, formData)
                    .then(() => {
                        const modal = document.getElementById('modal-documento');
                        const bsModal = bootstrap.Modal.getInstance(modal);
                        bsModal.hide();
                        formDoc.reset();
                        outroTipoDiv.style.display = 'none';
                        uploadDiv.style.display = 'block';
                        motivoAusenciaDiv.style.display = 'none';
                        Swal.fire('Sucesso', 'Documento adicionado com sucesso', 'success');
                    })
                    .catch(error => {
                        console.error('Erro ao adicionar documento:', error);
                        Swal.fire('Erro', error.message || 'Erro ao adicionar documento', 'error');
                    });
            });
        }

        documentosInitialized = true;
    }

    // API pública do módulo
    return {
        init: inicializarModulo,
        listarDocumentos: listarDocumentos,
        downloadDocumento: downloadDocumento,
        visualizarDocumento: visualizarDocumento,
        confirmarExclusao: confirmarExclusao,
        solicitarExclusao: solicitarExclusao,
        aprovarExclusao: aprovarExclusao
    };
})();
