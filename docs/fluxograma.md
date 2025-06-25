%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'background': '#1e293b',
      'primaryColor': '#a855f7',
      'secondaryColor': '#22c55e',
      'tertiaryColor': '#f43f5e',
      'quaternaryColor': '#3b82f6',
      'quinaryColor': '#eab308',
      'lineColor': '#94a3b8',
      'textColor': '#fff',
      'mainBkg': '#1e293b',
      'nodeBorder': 'none',
      'clusterBkg': 'transparent',
      'clusterBorder': 'none'
    }
  }
}%%

flowchart LR
    %% Estilos dos nós
    classDef inicio fill:#a855f7,stroke:none,color:#fff,rx:50,ry:50
    classDef processo1 fill:#22c55e,stroke:none,color:#fff,rx:50,ry:50
    classDef processo2 fill:#f43f5e,stroke:none,color:#fff,rx:50,ry:50
    classDef processo3 fill:#3b82f6,stroke:none,color:#fff,rx:50,ry:50
    classDef processo4 fill:#eab308,stroke:none,color:#fff,rx:50,ry:50

    %% Nós principais
    A((Início<br/>Balança)):::inicio
    
    %% Grupo 1 - Verde
    subgraph g1[" "]
        B1((Documentos<br/>Completos)):::processo1
        B2((Validação<br/>Inicial)):::processo1
        B3((Registro<br/>Base)):::processo1
    end
    
    %% Grupo 2 - Vermelho
    subgraph g2[" "]
        C1((Processo<br/>Produção)):::processo2
        C2((Controle<br/>Qualidade)):::processo2
    end
    
    %% Grupo 3 - Azul
    D((Conferência<br/>Final)):::processo3
    
    %% Grupo 4 - Amarelo
    subgraph g3[" "]
        E1((Aprovação<br/>Diretoria)):::processo4
        E2((Liberação<br/>Sistema)):::processo4
        E3((Arquivo<br/>Digital)):::processo4
        E4((Backup<br/>Cloud)):::processo4
    end

    %% Conexões
    A --> B1
    B1 --> B2
    B2 --> B3
    B3 --> C1
    C1 --> C2
    C2 --> D
    D --> E1
    E1 --> E2
    E2 --> E3
    E3 --> E4

    %% Estilo dos subgráficos
    style g1 fill:transparent,stroke:none
    style g2 fill:transparent,stroke:none
    style g3 fill:transparent,stroke:none

    %% Estilo das linhas
    linkStyle default stroke:#94a3b8,stroke-width:2px
