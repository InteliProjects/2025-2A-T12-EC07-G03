# Documentação Frontend - Flow Solutions

## Visão Geral

O frontend da Flow Solutions é uma aplicação React moderna desenvolvida para monitoramento em tempo real de equipamentos industriais (máquinas ITU). A aplicação fornece uma interface intuitiva para visualização de dados MQTT, status de máquinas, telemetria e alertas.

## Tecnologias Utilizadas

### Core Technologies
- **React 18.3.1**: Biblioteca para construção da interface
- **TypeScript 5.8.3**: Tipagem estática para maior segurança
- **Vite 5.4.19**: Build tool e dev server ultrarrápido
- **React Router DOM 6.30.1**: Roteamento client-side

### UI Framework & Styling
- **Tailwind CSS 3.4.17**: Framework CSS utility-first
- **Shadcn/ui**: Componentes acessíveis e customizáveis
- **Radix UI**: Primitivos de UI acessíveis
- **Lucide React**: Biblioteca de ícones

### Estado e Dados
- **TanStack Query 5.83.0**: Gerenciamento de estado servidor
- **Socket.IO Client**: Comunicação WebSocket em tempo real
- **React Hook Form 7.61.1**: Formulários performáticos
- **Zod 3.25.76**: Validação de esquemas

### Visualização
- **Recharts 2.15.4**: Gráficos e visualizações
- **React Day Picker**: Seleção de datas

## Arquitetura do Projeto

```
src/
├── components/          # Componentes reutilizáveis
│   ├── ui/             # Componentes base do Shadcn/ui
│   ├── Dashboard.tsx   # Dashboard principal
│   ├── MachineModal.tsx # Modal de detalhes da máquina
│   ├── LoginForm.tsx   # Formulário de login
│   └── ...
├── contexts/           # Contextos React
│   └── AuthContext.tsx # Contexto de autenticação
├── data/              # Dados mockados e tipos
│   └── mockData.ts    # Dados de demonstração
├── hooks/             # Hooks customizados
│   ├── useRealtimeData.tsx # Hook para dados MQTT
│   └── ...
├── lib/               # Utilitários
│   └── utils.ts       # Funções auxiliares
├── pages/             # Páginas da aplicação
│   ├── Dashboard.tsx  # Página do dashboard
│   ├── Index.tsx      # Página inicial/login
│   ├── Models.tsx     # Página de modelos ML
│   └── NotFound.tsx   # Página 404
└── App.tsx            # Componente raiz
```

## Principais Componentes

### 1. Dashboard (`components/Dashboard.tsx`)

O componente principal do sistema que exibe:

- **Cards de Máquinas**: Status em tempo real de cada equipamento ITU
- **Indicadores de Conexão**: Status MQTT (Conectado/Desconectado)
- **Telemetria**: RPM, tensão da bateria, pressão do óleo, etc.
- **Gráficos**: Visualização histórica de dados
- **Sidebar**: Navegação entre seções

**Funcionalidades:**
- Atualização em tempo real via WebSocket
- Filtragem de valores (mostra "--" quando não há dados)
- Sistema de cores para status (verde=conectado, vermelho=desconectado)
- Modal de detalhes ao clicar em uma máquina

```tsx
// Exemplo de uso dos dados
const formatValue = (value: number | undefined, unit: string = ''): string => {
  if (value === undefined || value === null) return '--';
  return `${value.toFixed(decimals)}${unit}`;
};
```

### 2. MachineModal (`components/MachineModal.tsx`)

Modal detalhado que exibe:

- **Informações Completas**: Todos os dados de telemetria
- **Status Detalhado**: Estado da máquina e conexão MQTT
- **Indicadores LED**: Status dos LEDs de controle
- **Localização**: Coordenadas GPS quando disponíveis
- **Alarmes e Eventos**: Histórico de ocorrências

### 3. useRealtimeData Hook (`hooks/useRealtimeData.tsx`)

Hook customizado para gerenciamento de dados em tempo real:

```tsx
const {
  machines,        // Array de máquinas com dados atuais
  summary,         // Resumo do dashboard
  mqttStatus,      // Status da conexão MQTT
  loading,         // Estado de carregamento
  error,           // Erros de conexão
  connected,       // Status da conexão WebSocket
  reconnect        // Função para reconectar
} = useRealtimeData();
```

**Características:**
- Conexão automática com WebSocket (localhost:4000)
- Reconexão automática em caso de falha
- Estado reativo para todas as atualizações
- Tratamento de erros robusto

### 4. AuthContext (`contexts/AuthContext.tsx`)

Contexto de autenticação que gerencia:

- **Estado do Usuário**: Informações do usuário logado
- **Login/Logout**: Funções de autenticação
- **Persistência**: Armazenamento local da sessão
- **Proteção de Rotas**: Controle de acesso

## Estrutura de Dados

### MachineData Interface

```tsx
interface MachineData {
  id: string;                    // Identificador único (ex: ITU-701)
  name: string;                  // Nome da máquina
  status: 'operando' | 'parada' | 'manutencao' | 'desconhecido' | 'desconectado';
  telemetry: {
    // Dados do Motor
    rpm?: number;                // Rotações por minuto
    bat?: number;                // Tensão da bateria (V)
    chave?: number;              // Tensão da chave (V)
    fuel_level?: number;         // Nível de combustível (L)
    fuel_consumption?: number;    // Consumo de combustível (L/h)
    oil_pressure?: number;       // Pressão do óleo (bar)
    oil_level?: number;          // Nível do óleo (%)
    coolant_temp?: number;       // Temperatura do líquido de arrefecimento (°C)
    engine_runtime_hours?: number; // Horas de funcionamento
    starts_number?: number;      // Número de partidas
    
    // Dados da Bomba
    recalque?: number;           // Pressão de recalque (bar)
    succao?: number;             // Pressão de sucção (bar)
    vibration?: number;          // Vibração (Hz)
    
    // Status dos LEDs
    led_auto?: number;           // LED automático (0/1)
    led_manual?: number;         // LED manual (0/1)
    led_stop?: number;           // LED parada (0/1)
    
    // Localização
    latitude?: number;           // Coordenada GPS
    longitude?: number;          // Coordenada GPS
  };
  lastUpdate: string;            // Timestamp da última atualização
  location: string;              // Descrição da localização
  alarms?: Array<{              // Array de alarmes
    message: string;
    timestamp: Date;
  }>;
  events?: Array<{              // Array de eventos
    message: string;
    timestamp: Date;
  }>;
}
```

### Dashboard Summary

```tsx
interface DashboardSummary {
  totalOperating: number;        // Total de máquinas operando
  machinesDown: number;          // Máquinas paradas/desconectadas
  activeAlerts: number;          // Alarmes ativos
  upcomingMaintenance: number;   // Manutenções pendentes
}
```

## Comunicação em Tempo Real

### WebSocket Integration

A aplicação se conecta com o backend via WebSocket para receber:

1. **Dados Iniciais**: Ao conectar, recebe estado atual de todas as máquinas
2. **Atualizações de Máquina**: Dados individuais quando há mudanças
3. **Resumo do Dashboard**: Estatísticas gerais atualizadas
4. **Status MQTT**: Estado da conexão com o broker MQTT

### Eventos WebSocket

```tsx
// Eventos recebidos do backend
socket.on('initialData', (data) => {
  // Dados iniciais: máquinas, resumo, status MQTT
});

socket.on('machineUpdate', (update) => {
  // Atualização de máquina específica
});

socket.on('summaryUpdate', (summary) => {
  // Novo resumo do dashboard
});

socket.on('mqttStatus', (status) => {
  // Status da conexão MQTT
});
```

## Roteamento

### Rotas Principais

- **`/`**: Página inicial com login
- **`/dashboard`**: Dashboard principal (requer autenticação)
- **`/models`**: Página de modelos de ML
- **`*`**: Página 404 para rotas não encontradas

### Proteção de Rotas

As rotas são protegidas pelo AuthContext, redirecionando usuários não autenticados para a página de login.

## Estilos e Temas

### Tailwind CSS

Utiliza sistema de classes utilitárias com configuração customizada:

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#1934A5",     // Azul principal
          foreground: "#ffffff"
        },
        // Outras cores...
      }
    }
  }
}
```

### Design System

- **Cores**: Paleta consistente com foco em azul corporativo
- **Tipografia**: Inter como fonte principal
- **Componentes**: Baseados no Shadcn/ui para consistência
- **Responsividade**: Mobile-first design
- **Acessibilidade**: Componentes Radix UI garantem acessibilidade

## Estados da Aplicação

### Loading States

- **Inicial**: Carregamento dos dados ao conectar
- **Reconexão**: Estado de reconexão WebSocket
- **Formulários**: Estados de submissão

### Error Handling

- **Conexão**: Tratamento de falhas de WebSocket
- **Dados**: Validação e fallbacks para dados inválidos
- **Autenticação**: Erros de login e sessão

### Data States

- **Undefined**: Dados não recebidos (mostra "--")
- **Zero**: Valor válido zero (mostra "0")
- **Null**: Dados inválidos (mostra "--")

## Performance

### Otimizações

1. **React.memo**: Componentes memorizados para evitar re-renders
2. **useMemo/useCallback**: Hooks de otimização onde necessário
3. **Lazy Loading**: Carregamento sob demanda de componentes
4. **Tree Shaking**: Vite elimina código não utilizado
5. **WebSocket Eficiente**: Apenas dados alterados são transmitidos

### Bundle Size

- **Vite**: Build otimizado e code splitting automático
- **Dependencies**: Apenas bibliotecas essenciais
- **Assets**: Imagens otimizadas e lazy loading

## Testes

### Estrutura de Testes (Recomendada)

```
tests/
├── components/         # Testes de componentes
├── hooks/             # Testes de hooks
├── integration/       # Testes de integração
└── utils/            # Testes de utilitários
```

### Ferramentas Sugeridas

- **Vitest**: Framework de testes rápido
- **React Testing Library**: Testes focados no usuário
- **MSW**: Mock Service Worker para APIs
- **Playwright**: Testes E2E

## Build e Deploy

### Comandos Disponíveis

```bash
# Desenvolvimento
npm run dev              # Inicia servidor de desenvolvimento

# Build
npm run build           # Build para produção
npm run build:dev       # Build modo desenvolvimento

# Qualidade
npm run lint            # Executa ESLint
npm run preview         # Preview da build local
```

### Configuração de Build

- **Vite**: Configuração otimizada para produção
- **TypeScript**: Verificação de tipos no build
- **ESLint**: Linting automático
- **PostCSS**: Processamento de CSS

### Deploy

Compatível com qualquer provedor que suporte aplicações React:

- **Vercel**: Deploy automático via Git
- **Netlify**: Build e deploy contínuo
- **AWS S3 + CloudFront**: Hospedagem estática
- **Docker**: Containerização para deploy

## Manutenção e Desenvolvimento

### Padrões de Código

1. **TypeScript**: Tipagem forte obrigatória
2. **ESLint**: Regras rigorosas de qualidade
3. **Prettier**: Formatação automática
4. **Conventional Commits**: Mensagens de commit padronizadas

### Estrutura de Componentes

```tsx
// Exemplo de estrutura padrão
interface ComponentProps {
  // Props tipadas
}

export const Component: React.FC<ComponentProps> = ({ 
  prop1, 
  prop2 
}) => {
  // Hooks
  // Estados locais
  // Funções auxiliares
  
  return (
    // JSX
  );
};
```

### Boas Práticas

1. **Componentes Pequenos**: Responsabilidade única
2. **Hooks Customizados**: Lógica reutilizável
3. **TypeScript Strict**: Configuração rigorosa
4. **Accessibility**: Sempre considerar acessibilidade
5. **Performance**: Otimizar quando necessário
6. **Testing**: Testes para funcionalidades críticas

## Troubleshooting

### Problemas Comuns

1. **WebSocket Não Conecta**: Verificar se backend está rodando na porta 4000
2. **Dados Não Aparecem**: Verificar console para erros de MQTT
3. **Build Falha**: Verificar tipos TypeScript
4. **Estilos Quebrados**: Limpar cache do Tailwind

### Debug

```tsx
// Debug de dados em tempo real
console.log('Machines:', machines);
console.log('WebSocket Connected:', connected);
console.log('MQTT Status:', mqttStatus);
```

### Logs Úteis

- **Network Tab**: Verificar requests e WebSocket
- **Console**: Erros JavaScript e logs customizados
- **React DevTools**: Estado dos componentes
- **Redux DevTools**: Estado global (se aplicável)

## Próximos Passos

### Melhorias Sugeridas

1. **Testes Automatizados**: Implementar suite completa
2. **PWA**: Transformar em Progressive Web App
3. **Offline Mode**: Cache local para funcionamento offline
4. **Analytics**: Instrumentação com Google Analytics
5. **Error Tracking**: Integração com Sentry
6. **Performance Monitoring**: Core Web Vitals

### Novas Funcionalidades

1. **Alertas em Tempo Real**: Notificações push
2. **Relatórios**: Geração de PDFs
3. **Configurações**: Painel de configuração de usuário
4. **Multi-tenancy**: Suporte a múltiplos clientes
5. **Mapas**: Visualização geográfica das máquinas

---

**Versão**: 1.0  
**Última Atualização**: Outubro 2025  
**Autor**: Equipe de Desenvolvimento Flow Solutions