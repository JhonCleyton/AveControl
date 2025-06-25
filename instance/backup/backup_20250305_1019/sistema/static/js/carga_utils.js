// Funções para manipulação de subcargas
let contadorSubcargas = 0;

function adicionarSubcarga() {
    const template = document.getElementById('template-subcarga');
    const container = document.getElementById('subcargas-container');
    const clone = template.content.cloneNode(true);
    
    contadorSubcargas++;
    clone.querySelector('.numero-subcarga').textContent = contadorSubcargas;
    
    container.appendChild(clone);
}

// Função para coletar dados do formulário
function coletarDadosFormulario() {
    const dados = {
        numero_carga: document.getElementById('numero_carga').value,
        tipo_ave: document.getElementById('tipo_ave').value,
        data_abate: document.getElementById('data_abate').value,
        dia_semana: document.getElementById('dia_semana').value,
        motorista: document.getElementById('motorista').value === 'outro' ? 
            document.getElementById('motorista_outro').value : 
            document.getElementById('motorista').value,
        transportadora: document.getElementById('transportadora').value,
        placa_veiculo: document.getElementById('transportadora').value === 'Ellen Transportes' ?
            document.getElementById('placa_veiculo').value :
            document.getElementById('placa_veiculo_input').value,
        valor_km: parseFloat(document.getElementById('valor_km').value) || 0,
        km_saida: parseFloat(document.getElementById('km_saida').value) || 0,
        km_chegada: parseFloat(document.getElementById('km_chegada').value) || 0,
        km_rodados: parseFloat(document.getElementById('km_rodados').value) || 0,
        caixas_vazias: parseInt(document.getElementById('caixas_vazias').value) || 0,
        produtor: document.getElementById('produtor').value,
        uf_produtor: document.getElementById('uf_produtor').value,
        numero_nfe: document.getElementById('numero_nfe').value,
        data_nfe: document.getElementById('data_nfe').value,
        numero_gta: document.getElementById('numero_gta').value,
        data_gta: document.getElementById('data_gta').value,
        peso_granja: parseFloat(document.getElementById('peso_granja').value) || 0,
        peso_frigorifico: parseFloat(document.getElementById('peso_frigorifico').value) || 0,
        quebra_peso: parseFloat(document.getElementById('quebra_peso').value) || 0,
        percentual_quebra: parseFloat(document.getElementById('percentual_quebra').value) || 0,
        motivo_alta_quebra: document.getElementById('motivo_alta_quebra').value,
        valor_frete: parseFloat(document.getElementById('valor_frete').value) || 0,
        pedagios: parseFloat(document.getElementById('pedagios').value) || 0,
        outras_despesas: parseFloat(document.getElementById('outras_despesas').value) || 0,
        abastecimento_empresa: parseFloat(document.getElementById('abastecimento_empresa').value) || 0,
        abastecimento_posto: parseFloat(document.getElementById('abastecimento_posto').value) || 0,
        adiantamento: parseFloat(document.getElementById('adiantamento').value) || 0,
        valor_pagar: parseFloat(document.getElementById('valor_pagar').value) || 0,
        subcargas: []
    };

    // Coletar dados das subcargas
    const subcargas = document.querySelectorAll('.subcarga');
    subcargas.forEach(item => {
        dados.subcargas.push({
            tipo_ave: item.querySelector('[id^="tipo_ave_subcarga"]').value,
            produtor: item.querySelector('[id^="produtor_subcarga"]').value,
            uf_produtor: item.querySelector('[id^="uf_produtor_subcarga"]').value,
            numero_nfe: item.querySelector('[id^="numero_nfe_subcarga"]').value,
            data_nfe: item.querySelector('[id^="data_nfe_subcarga"]').value,
            numero_gta: item.querySelector('[id^="numero_gta_subcarga"]').value,
            data_gta: item.querySelector('[id^="data_gta_subcarga"]').value,
            peso_granja: parseFloat(item.querySelector('[id^="peso_granja_subcarga"]').value) || 0,
            peso_frigorifico: parseFloat(item.querySelector('[id^="peso_frigorifico_subcarga"]').value) || 0,
            quebra_peso: parseFloat(item.querySelector('[id^="quebra_peso_subcarga"]').value) || 0,
            percentual_quebra: parseFloat(item.querySelector('[id^="percentual_quebra_subcarga"]').value) || 0
        });
    });

    return dados;
}

// Função para validar dados do formulário
function validarDadosFormulario(dados, isRascunho = false) {
    const camposObrigatorios = [
        { campo: 'numero_carga', nome: 'Número da Carga' },
        { campo: 'tipo_ave', nome: 'Tipo de Ave' },
        { campo: 'data_abate', nome: 'Data de Abate' },
        { campo: 'motorista', nome: 'Motorista' },
        { campo: 'transportadora', nome: 'Transportadora' },
        { campo: 'placa_veiculo', nome: 'Placa do Veículo' },
        { campo: 'produtor', nome: 'Produtor' },
        { campo: 'numero_gta', nome: 'Número da GTA' },
        { campo: 'data_gta', nome: 'Data da GTA' }
    ];

    if (!isRascunho) {
        camposObrigatorios.push(
            { campo: 'km_saida', nome: 'KM Saída' },
            { campo: 'km_chegada', nome: 'KM Chegada' },
            { campo: 'peso_granja', nome: 'Peso na Granja' },
            { campo: 'peso_frigorifico', nome: 'Peso no Frigorífico' }
        );
    }

    const camposFaltantes = camposObrigatorios.filter(({ campo, nome }) => {
        const valor = dados[campo];
        return valor === undefined || valor === null || 
               (typeof valor === 'string' && valor.trim() === '') ||
               (typeof valor === 'number' && isNaN(valor));
    });

    if (camposFaltantes.length > 0) {
        throw new Error('Os seguintes campos são obrigatórios: ' + 
            camposFaltantes.map(c => c.nome).join(', '));
    }

    return true;
}

// Função para salvar carga
async function salvarCarga() {
    try {
        const dados = coletarDadosFormulario();
        validarDadosFormulario(dados);

        const response = await fetch('/cargas/criar_carga', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dados)
        });

        const result = await response.json();

        if (response.ok) {
            // Se o módulo de documentos existe, inicializar com o ID da carga
            if (result.id && window.DocumentosModule) {
                window.DocumentosModule.listarDocumentos(result.id);
            }
            
            await Swal.fire({
                icon: 'success',
                title: 'Sucesso!',
                text: 'Carga salva com sucesso!'
            });
            window.location.href = '/cargas';
        } else {
            throw new Error(result.message || 'Erro ao salvar a carga');
        }
    } catch (error) {
        console.error('Erro ao salvar carga:', error);
        Swal.fire({
            icon: 'error',
            title: 'Erro!',
            text: error.message
        });
    }
}

// Função para salvar rascunho
async function salvarRascunho() {
    try {
        const dados = coletarDadosFormulario();
        validarDadosFormulario(dados, true);

        const response = await fetch('/cargas/salvar_rascunho', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dados)
        });

        const result = await response.json();

        if (response.ok) {
            await Swal.fire({
                icon: 'success',
                title: 'Sucesso!',
                text: 'Rascunho salvo com sucesso!'
            });
            window.location.href = '/cargas';
        } else {
            throw new Error(result.error || 'Erro ao salvar o rascunho');
        }
    } catch (error) {
        console.error('Erro ao salvar rascunho:', error);
        Swal.fire({
            icon: 'error',
            title: 'Erro!',
            text: error.message
        });
    }
}

// Função para limpar formulário
async function limparCargas() {
    const result = await Swal.fire({
        title: 'Tem certeza?',
        text: "Todos os dados do formulário serão perdidos!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sim, limpar!',
        cancelButtonText: 'Cancelar'
    });

    if (result.isConfirmed) {
        // Limpar campos do formulário principal
        document.querySelectorAll('input, select, textarea').forEach(element => {
            if (element.type === 'number') {
                element.value = '0';
            } else if (element.type !== 'button' && element.type !== 'submit') {
                element.value = '';
            }
            if (element.tagName === 'SELECT') {
                element.selectedIndex = 0;
            }
        });

        // Remover subcargas
        const subcargasContainer = document.getElementById('subcargas-container');
        subcargasContainer.innerHTML = '';
        window.contadorSubcargas = 0;
        document.getElementById('btnAddSubcarga').disabled = false;

        // Resetar estados dos campos especiais
        document.getElementById('outro-motorista-div').style.display = 'none';
        document.getElementById('div_motivo_quebra').style.display = 'none';
        
        // Recarregar número da carga
        carregarNumeroCarga();

        Swal.fire(
            'Limpo!',
            'O formulário foi limpo com sucesso.',
            'success'
        );
    }
}

// Adicionar event listeners para os botões de ação
document.addEventListener('DOMContentLoaded', function() {
    const btnSalvarCarga = document.getElementById('btnSalvarCarga');
    const btnSalvarRascunho = document.getElementById('btnSalvarRascunho');
    const btnLimparCargas = document.getElementById('btnLimparCargas');
    
    if (btnSalvarCarga) {
        btnSalvarCarga.addEventListener('click', salvarCarga);
    }
    
    if (btnSalvarRascunho) {
        btnSalvarRascunho.addEventListener('click', salvarRascunho);
    }
    
    if (btnLimparCargas) {
        btnLimparCargas.addEventListener('click', limparCargas);
    }
});

// Exportar funções para uso global
window.adicionarSubcarga = adicionarSubcarga;
window.salvarCarga = salvarCarga;
window.salvarRascunho = salvarRascunho;
window.limparCargas = limparCargas;
