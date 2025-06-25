let chatAtual = 'grupo';
let ultimaDataExibida = null;
let ultimoAutor = null;
let socket = io();

// Conecta ao socket
socket.on('connect', () => {
    console.log('Conectado ao servidor');
});

// Recebe mensagens
socket.on('nova_mensagem', (data) => {
    adicionarMensagem(data);
    rolarParaBaixo();
    
    // Se a mensagem não é do usuário atual, marca como não lida
    if (data.id_usuario !== currentUserId) {
        buscarMensagensNaoLidas();
    }
});

// Função para formatar data
function formatarData(data) {
    const dataObj = new Date(data);
    const hoje = new Date();
    const ontem = new Date(hoje);
    ontem.setDate(hoje.getDate() - 1);

    if (dataObj.toDateString() === hoje.toDateString()) {
        return 'Hoje';
    } else if (dataObj.toDateString() === ontem.toDateString()) {
        return 'Ontem';
    } else {
        return dataObj.toLocaleDateString('pt-BR');
    }
}

// Função para formatar hora
function formatarHora(data) {
    const dataObj = new Date(data);
    return dataObj.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

// Função para criar grupo de data
function criarGrupoData(data) {
    const dataFormatada = formatarData(data);
    if (dataFormatada !== ultimaDataExibida) {
        ultimaDataExibida = dataFormatada;
        return `<div class="message-group"><div class="message-date"><span>${dataFormatada}</span></div>`;
    }
    return '';
}

// Função para adicionar mensagem
function adicionarMensagem(mensagem) {
    const mensagensDiv = document.getElementById('mensagens');
    const dataAtual = new Date(mensagem.data_envio);
    let html = criarGrupoData(dataAtual);
    
    const isEnviada = mensagem.id_usuario === currentUserId;
    const mostrarAutor = !isEnviada && mensagem.autor !== ultimoAutor;
    
    html += `
        <div class="mensagem ${isEnviada ? 'enviada' : ''}">
            <div class="mensagem-conteudo">
                ${mostrarAutor ? `<div class="mensagem-autor">${mensagem.autor}</div>` : ''}
                <div class="mensagem-texto">${mensagem.conteudo}</div>
                <div class="mensagem-info">
                    <span class="mensagem-hora">${formatarHora(mensagem.data_envio)}</span>
                </div>
            </div>
        </div>
    `;

    if (html.includes('message-group')) {
        mensagensDiv.insertAdjacentHTML('beforeend', html);
    } else {
        const ultimoGrupo = mensagensDiv.querySelector('.message-group:last-child');
        if (ultimoGrupo) {
            ultimoGrupo.insertAdjacentHTML('beforeend', html);
        } else {
            mensagensDiv.insertAdjacentHTML('beforeend', `<div class="message-group">${html}</div>`);
        }
    }

    ultimoAutor = mensagem.autor;
    
    // Se a mensagem não é do usuário atual e está no chat atual, marca como lida
    if (!isEnviada && mensagem.id) {
        marcarComoLida(mensagem.id);
    }
}

// Função para rolar para baixo
function rolarParaBaixo() {
    const mensagensDiv = document.getElementById('mensagens');
    mensagensDiv.scrollTop = mensagensDiv.scrollHeight;
}

// Função para trocar de chat
function trocarChat(novoChat) {
    // Remove a classe active do chat atual
    const chatAtualElement = document.getElementById(`chat-${chatAtual}`);
    if (chatAtualElement) {
        chatAtualElement.classList.remove('active');
    }

    // Adiciona a classe active ao novo chat
    const novoChatElement = document.getElementById(`chat-${novoChat}`);
    if (novoChatElement) {
        novoChatElement.classList.add('active');
    }

    // Atualiza o cabeçalho do chat
    const chatHeader = document.querySelector('.chat-main-header');
    const chatInfo = novoChatElement.querySelector('.chat-item-info').cloneNode(true);
    const chatAvatar = novoChatElement.querySelector('.chat-item-avatar').cloneNode(true);
    
    chatHeader.innerHTML = '';
    chatHeader.appendChild(chatAvatar);
    chatHeader.appendChild(chatInfo);

    // Limpa as mensagens anteriores
    document.getElementById('mensagens').innerHTML = '';
    
    // Atualiza o chat atual
    chatAtual = novoChat;
    ultimaDataExibida = null;
    ultimoAutor = null;

    // Carrega as mensagens do novo chat
    fetch(`/chat/mensagens/${novoChat}`)
        .then(response => response.json())
        .then(mensagens => {
            mensagens.forEach(mensagem => {
                adicionarMensagem(mensagem);
            });
            rolarParaBaixo();
            
            // Atualiza contadores de mensagens não lidas
            buscarMensagensNaoLidas();
        });
        
    // Sai da sala anterior e entra na nova sala
    if (chatAtual !== novoChat) {
        socket.emit('sair_sala', chatAtual);
        socket.emit('entrar_sala', novoChat);
    }
}

// Função para enviar mensagem
function enviarMensagem(event) {
    event.preventDefault();
    const input = document.getElementById('mensagem-input');
    const mensagem = input.value.trim();
    
    if (mensagem) {
        const token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        fetch('/chat/enviar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': token
            },
            body: JSON.stringify({
                mensagem: mensagem,
                destinatario: chatAtual
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao enviar mensagem');
            }
            input.value = '';
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao enviar mensagem');
        });
    }
}

// Função para buscar mensagens não lidas
function buscarMensagensNaoLidas() {
    fetch('/chat/mensagens_nao_lidas')
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                atualizarContadores(data);
            }
        })
        .catch(error => {
            console.error('Erro ao atualizar notificações do chat:', error);
        });
}

// Função para atualizar contadores
function atualizarContadores(data) {
    // Atualiza contador do grupo
    const badgeGrupo = document.querySelector('#chat-grupo .chat-item-time');
    if (badgeGrupo) {
        badgeGrupo.textContent = data.grupo > 0 ? `${data.grupo} não lida(s)` : '';
    }
    
    // Atualiza contadores individuais
    Object.entries(data.individuais || {}).forEach(([userId, count]) => {
        const badge = document.querySelector(`#chat-${userId} .chat-item-time`);
        if (badge) {
            badge.textContent = count > 0 ? `${count} não lida(s)` : '';
        }
    });
}

// Função para marcar mensagem como lida
function marcarComoLida(mensagemId) {
    const token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    fetch(`/chat/marcar_como_lida/${mensagemId}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': token
        }
    })
    .then(() => {
        buscarMensagensNaoLidas();
    })
    .catch(error => {
        console.error('Erro ao marcar mensagem como lida:', error);
    });
}

// Função para abrir modal de edição de perfil
function abrirEditarPerfil() {
    carregarIcones();
    const modal = new bootstrap.Modal(document.getElementById('modalEditarPerfil'));
    modal.show();
}

// Função para carregar ícones
function carregarIcones() {
    fetch('/chat/icones')
        .then(response => response.json())
        .then(icones => {
            const container = document.getElementById('icones-container');
            container.innerHTML = '';
            
            icones.forEach(icone => {
                const div = document.createElement('div');
                div.className = 'icon-item';
                div.innerHTML = `<img src="/static/icons/${icone}" alt="${icone}">`;
                div.onclick = () => selecionarIcone(div, icone);
                container.appendChild(div);
            });
        });
}

// Função para selecionar ícone
function selecionarIcone(elemento, icone) {
    document.querySelectorAll('.icon-item').forEach(item => {
        item.classList.remove('selected');
    });
    elemento.classList.add('selected');
    window.iconeSelectionado = icone;
}

// Função para salvar perfil
function salvarPerfil() {
    const token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const nomeExibicao = document.getElementById('nome_exibicao').value;
    
    fetch('/chat/perfil/editar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': token
        },
        body: JSON.stringify({
            nome_exibicao: nomeExibicao,
            icone_perfil: window.iconeSelectionado
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro ao salvar perfil');
        }
        return response.json();
    })
    .then(data => {
        location.reload();
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro ao salvar perfil');
    });
}

// Atualização periódica de mensagens não lidas
setInterval(buscarMensagensNaoLidas, 10000);

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    // Carrega as mensagens iniciais
    trocarChat('grupo');
    
    // Configura o socket para a sala inicial
    socket.emit('entrar_sala', 'grupo');
    
    // Busca mensagens não lidas
    buscarMensagensNaoLidas();
});
