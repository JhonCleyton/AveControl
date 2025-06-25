// Variáveis globais
let contadorSubcargas = 0;
const MAX_SUBCARGAS = 2;

// Função para carregar número da carga
async function carregarNumeroCarga() {
    try {
        const response = await fetch('/cargas/proximo_numero');
        const data = await response.json();
        if (data.success) {
            document.getElementById('numero_carga').value = data.numero;
        } else {
            console.error('Erro ao carregar número da carga:', data.error);
        }
    } catch (error) {
        console.error('Erro ao carregar número da carga:', error);
    }
}

// Função para atualizar dia da semana
function atualizarDiaSemana() {
    const dataAbateInput = document.getElementById('data_abate');
    const diaSemanaInput = document.getElementById('dia_semana');
    
    if (!dataAbateInput || !diaSemanaInput) return;
    
    if (dataAbateInput.value) {
        const [ano, mes, dia] = dataAbateInput.value.split('-');
        const data = new Date(ano, mes - 1, dia);
        const diasSemana = ['Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado'];
        diaSemanaInput.value = diasSemana[data.getDay()];
    } else {
        diaSemanaInput.value = '';
    }
}

// Função para alternar campo de outro motorista
function toggleOutroMotorista() {
    const motoristaSelect = document.getElementById('motorista');
    const outroMotoristaDiv = document.getElementById('outro-motorista-div');
    const motoristaOutroInput = document.getElementById('motorista_outro');
    
    if (motoristaSelect.value === 'outro') {
        outroMotoristaDiv.style.display = 'block';
        motoristaOutroInput.required = true;
    } else {
        outroMotoristaDiv.style.display = 'none';
        motoristaOutroInput.required = false;
        motoristaOutroInput.value = '';
    }
}

// Função para alternar campos de placa baseado na transportadora
function togglePlacaVeiculo() {
    const transportadoraSelect = document.getElementById('transportadora');
    const placaSelect = document.getElementById('placa_veiculo');
    const placaInput = document.getElementById('placa_veiculo_input');
    const valorKmInput = document.getElementById('valor_km');
    
    if (transportadoraSelect.value === 'Ellen Transportes') {
        placaSelect.style.display = 'block';
        placaInput.style.display = 'none';
        placaInput.value = '';
        valorKmInput.readOnly = true;
        carregarVeiculos(); // Carregar veículos quando selecionar Ellen Transportes
    } else if (transportadoraSelect.value === 'Terceirizado') {
        placaSelect.style.display = 'none';
        placaInput.style.display = 'block';
        placaSelect.value = '';
        valorKmInput.readOnly = false;
        valorKmInput.value = '';
    } else {
        placaSelect.style.display = 'none';
        placaInput.style.display = 'none';
        placaSelect.value = '';
        placaInput.value = '';
        valorKmInput.readOnly = false;
        valorKmInput.value = '';
    }
    calcularValorFrete();
}

// Função para carregar veículos baseado na transportadora
async function carregarVeiculos() {
    try {
        const transportadora = document.getElementById('transportadora').value;
        const placaSelect = document.getElementById('placa_veiculo');
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        // Limpar opções atuais
        placaSelect.innerHTML = '<option value="">Selecione a placa</option>';
        
        if (transportadora === 'Ellen Transportes') {
            const response = await fetch(`/cargas/veiculos?transportadora=${encodeURIComponent(transportadora)}`, {
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const placas = await response.json();
            
            placas.forEach(placa => {
                const option = document.createElement('option');
                option.value = placa;
                option.textContent = placa;
                placaSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar veículos:', error);
        // Adicionar uma opção de erro
        const option = document.createElement('option');
        option.value = "";
        option.textContent = "Erro ao carregar placas";
        placaSelect.appendChild(option);
    }
}

// Função para calcular quebra de peso
function calcularQuebraPeso() {
    const pesoGranja = parseFloat(document.getElementById('peso_granja').value) || 0;
    const pesoFrigorifico = parseFloat(document.getElementById('peso_frigorifico').value) || 0;
    
    if (pesoGranja > 0 && pesoFrigorifico > 0) {
        const quebraPeso = pesoGranja - pesoFrigorifico;
        const percentualQuebra = ((quebraPeso / pesoGranja) * 100);
        
        document.getElementById('quebra_peso').value = quebraPeso.toFixed(2);
        document.getElementById('percentual_quebra').value = percentualQuebra.toFixed(2);
        
        // Verificar se a quebra está acima de 5%
        const divMotivoQuebra = document.getElementById('div_motivo_quebra');
        const motivoAltaQuebra = document.getElementById('motivo_alta_quebra');
        
        if (percentualQuebra > 5) {
            divMotivoQuebra.style.display = 'block';
            motivoAltaQuebra.required = true;
        } else {
            divMotivoQuebra.style.display = 'none';
            motivoAltaQuebra.required = false;
            motivoAltaQuebra.value = '';
        }
    } else {
        document.getElementById('quebra_peso').value = '';
        document.getElementById('percentual_quebra').value = '';
        document.getElementById('div_motivo_quebra').style.display = 'none';
        document.getElementById('motivo_alta_quebra').value = '';
    }
}

// Função para calcular KM rodados
function calcularKmRodados() {
    const kmSaida = parseFloat(document.getElementById('km_saida').value) || 0;
    const kmChegada = parseFloat(document.getElementById('km_chegada').value) || 0;
    
    if (kmChegada >= kmSaida) {
        const kmRodados = kmChegada - kmSaida;
        document.getElementById('km_rodados').value = kmRodados.toFixed(2);
        calcularValorFrete();
    } else {
        document.getElementById('km_rodados').value = '';
        document.getElementById('valor_frete').value = '';
        document.getElementById('valor_frete_fechamento').value = '';
        document.getElementById('valor_pagar').value = '';
    }
}

// Função para calcular valor do frete
function calcularValorFrete() {
    const kmRodados = parseFloat(document.getElementById('km_rodados').value) || 0;
    const valorKm = parseFloat(document.getElementById('valor_km').value) || 0;
    
    if (kmRodados > 0 && valorKm > 0) {
        const valorFrete = kmRodados * valorKm;
        document.getElementById('valor_frete').value = valorFrete.toFixed(2);
        document.getElementById('valor_frete_fechamento').value = valorFrete.toFixed(2);
        calcularValorPagar();
    }
}

// Função para calcular valor a pagar
function calcularValorPagar() {
    const valorFrete = parseFloat(document.getElementById('valor_frete').value) || 0;
    const pedagios = parseFloat(document.getElementById('pedagios').value) || 0;
    const outrasDespesas = parseFloat(document.getElementById('outras_despesas').value) || 0;
    const abastecimentoEmpresa = parseFloat(document.getElementById('abastecimento_empresa').value) || 0;
    const abastecimentoPosto = parseFloat(document.getElementById('abastecimento_posto').value) || 0;
    const adiantamento = parseFloat(document.getElementById('adiantamento').value) || 0;

    const valorPagar = valorFrete + pedagios + outrasDespesas - abastecimentoEmpresa - abastecimentoPosto - adiantamento;
    document.getElementById('valor_pagar').value = valorPagar.toFixed(2);
}

// Função para adicionar subcarga
function adicionarSubcarga() {
    if (contadorSubcargas >= MAX_SUBCARGAS) {
        Swal.fire({
            icon: 'warning',
            title: 'Limite atingido',
            text: 'Máximo de ' + MAX_SUBCARGAS + ' subcargas permitido.'
        });
        return;
    }

    contadorSubcargas++;
    const container = document.getElementById('subcargas-container');
    const template = document.getElementById('template-subcarga');
    const clone = template.content.cloneNode(true);
    
    // Atualizar número da subcarga
    clone.querySelector('.numero-subcarga').textContent = contadorSubcargas;
    
    // Adicionar event listeners para cálculos de peso da subcarga
    const pesoGranjaSubcarga = clone.querySelector('[id^="peso_granja_subcarga"]');
    const pesoFrigorificoSubcarga = clone.querySelector('[id^="peso_frigorifico_subcarga"]');
    
    if (pesoGranjaSubcarga && pesoFrigorificoSubcarga) {
        [pesoGranjaSubcarga, pesoFrigorificoSubcarga].forEach(input => {
            input.addEventListener('input', function() {
                const pesoGranja = parseFloat(pesoGranjaSubcarga.value) || 0;
                const pesoFrigorifico = parseFloat(pesoFrigorificoSubcarga.value) || 0;
                
                if (pesoGranja > 0 && pesoFrigorifico > 0) {
                    const quebraPeso = pesoGranja - pesoFrigorifico;
                    const percentualQuebra = (quebraPeso / pesoGranja) * 100;
                    
                    clone.querySelector('[id^="quebra_peso_subcarga"]').value = quebraPeso.toFixed(2);
                    clone.querySelector('[id^="percentual_quebra_subcarga"]').value = percentualQuebra.toFixed(2);
                }
            });
        });
    }
    
    container.appendChild(clone);
    
    if (contadorSubcargas >= MAX_SUBCARGAS) {
        document.getElementById('btnAdicionarSubcarga').disabled = true;
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Carregar número da carga
    carregarNumeroCarga();

    // Event listener para data de abate
    const dataAbateInput = document.getElementById('data_abate');
    if (dataAbateInput) {
        dataAbateInput.addEventListener('change', atualizarDiaSemana);
        
        // Se já tiver uma data, atualiza o dia da semana
        if (dataAbateInput.value) {
            atualizarDiaSemana();
        }
    }

    // Event listener para motorista
    const motoristaSelect = document.getElementById('motorista');
    if (motoristaSelect) {
        motoristaSelect.addEventListener('change', toggleOutroMotorista);
    }

    // Event listener para transportadora
    const transportadoraSelect = document.getElementById('transportadora');
    if (transportadoraSelect) {
        transportadoraSelect.addEventListener('change', togglePlacaVeiculo);
    }

    // Event listeners para campos de peso
    const pesoInputs = ['peso_granja', 'peso_frigorifico'];
    pesoInputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('input', calcularQuebraPeso);
        }
    });

    // Event listeners para campos de KM
    const kmInputs = ['km_saida', 'km_chegada'];
    kmInputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('input', calcularKmRodados);
        }
    });

    // Event listeners para campos de valor
    const valorInputs = ['pedagios', 'outras_despesas', 'abastecimento_empresa', 'abastecimento_posto', 'adiantamento'];
    valorInputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('input', calcularValorPagar);
        }
    });

    // Event listener para valor do KM
    const valorKmInput = document.getElementById('valor_km');
    if (valorKmInput) {
        valorKmInput.addEventListener('input', function() {
            calcularValorFrete();
            calcularValorPagar();
        });
    }

    // Event listener para botão de adicionar subcarga
    const btnAdicionarSubcarga = document.getElementById('btnAdicionarSubcarga');
    if (btnAdicionarSubcarga) {
        btnAdicionarSubcarga.addEventListener('click', adicionarSubcarga);
    }
});
