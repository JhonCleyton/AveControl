// Gerenciador de temas
const themeManager = {
    // Temas disponíveis
    themes: {
        claro: {
            bodyBg: '#f8f9fa',
            textColor: '#212529',
            cardBg: '#ffffff',
            cardHeaderBg: '#f8f9fa',
            navbarBg: '#343a40',
            navbarText: '#ffffff',
            linkColor: '#0d6efd',
            borderColor: 'rgba(0,0,0,0.1)',
            inputBg: '#ffffff',
            inputText: '#212529'
        },
        escuro: {
            bodyBg: '#1a1d20',
            textColor: '#e9ecef',
            cardBg: '#2c3034',
            cardHeaderBg: '#212529',
            navbarBg: '#212529',
            navbarText: '#ffffff',
            linkColor: '#6ea8fe',
            borderColor: 'rgba(255,255,255,0.1)',
            inputBg: '#2c3034',
            inputText: '#e9ecef'
        }
    },

    // Aplica o tema
    applyTheme: function(theme) {
        const root = document.documentElement;
        const themeColors = this.themes[theme];

        // Aplica as variáveis CSS
        root.style.setProperty('--body-bg', themeColors.bodyBg);
        root.style.setProperty('--text-color', themeColors.textColor);
        root.style.setProperty('--card-bg', themeColors.cardBg);
        root.style.setProperty('--card-header-bg', themeColors.cardHeaderBg);
        root.style.setProperty('--navbar-bg', themeColors.navbarBg);
        root.style.setProperty('--navbar-text', themeColors.navbarText);
        root.style.setProperty('--link-color', themeColors.linkColor);
        root.style.setProperty('--border-color', themeColors.borderColor);
        root.style.setProperty('--input-bg', themeColors.inputBg);
        root.style.setProperty('--input-text', themeColors.inputText);

        // Atualiza classes do Bootstrap
        document.body.classList.remove('bg-light', 'bg-dark');
        document.body.classList.add(theme === 'escuro' ? 'bg-dark' : 'bg-light');

        // Atualiza a navbar
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            navbar.classList.remove('navbar-light', 'navbar-dark');
            navbar.classList.remove('bg-light', 'bg-dark');
            navbar.classList.add('navbar-dark');
            navbar.classList.add('bg-dark');
        }

        // Salva a preferência no localStorage
        localStorage.setItem('theme', theme);
    },

    // Inicializa o tema
    init: function() {
        // Pega o tema do usuário do backend ou usa o padrão
        const userTheme = document.body.dataset.theme || 'claro';
        this.applyTheme(userTheme);

        // Adiciona listener para mudanças no select de tema
        const themeSelect = document.getElementById('tema');
        if (themeSelect) {
            themeSelect.addEventListener('change', (e) => {
                this.applyTheme(e.target.value);
            });
        }
    }
};

// Inicializa quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    themeManager.init();
});
