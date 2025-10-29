// Mock data for dashboard - easily replaceable with real API calls later

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

export interface MachineStatus {
  id: string;
  name: string;
  status: 'operando' | 'parada' | 'manutencao';
  telemetry: {
    rpm: number;
    bat: number;
    chave: number;
    out: number;
  };
  lastUpdate: string;
  location: string;
}

export interface Alert {
  id: string;
  machineId: string;
  machineName: string;
  type: 'critico' | 'aviso';
  messages: string[];
  timestamp: string;
}

export interface DashboardSummary {
  totalOperating: number;
  machinesDown: number;
  activeAlerts: number;
  upcomingMaintenance: number;
}

export interface ChartData {
  time: string;
  itu101: number;
  itu102: number;
  itu103: number;
  itu117: number;
}

// Mock user data
export const mockUser: User = {
  id: '1',
  name: 'Bruno',
  email: 'grupo03@inteli.edu.br',
  avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=40&h=40&fit=crop&crop=face'
};

// Mock dashboard summary
export const mockDashboardSummary: DashboardSummary = {
  totalOperating: 15,
  machinesDown: 10,
  activeAlerts: 2,
  upcomingMaintenance: 3
};

// Mock machine status data
export const mockMachineStatus: MachineStatus[] = [
  {
    id: 'itu-692',
    name: 'ITU-692',
    status: 'operando',
    telemetry: {
      rpm: 1950,
      bat: 25,
      chave: 13,
      out: 40
    },
    lastUpdate: '2 minutos',
    location: 'Principais dados de telemetria'
  },
  {
    id: 'itu-701',
    name: 'ITU-701',
    status: 'operando',
    telemetry: {
      rpm: 1950,
      bat: 25,
      chave: 13,
      out: 40
    },
    lastUpdate: '30 segundos',
    location: 'Principais dados de telemetria'
  },
  {
    id: 'itu-692-2',
    name: 'ITU-692',
    status: 'parada',
    telemetry: {
      rpm: 0,
      bat: 0,
      chave: 0,
      out: 0
    },
    lastUpdate: '2 horas',
    location: 'Principais dados de telemetria'
  },
  {
    id: 'itu-701-2',
    name: 'ITU-701',
    status: 'operando',
    telemetry: {
      rpm: 1950,
      bat: 25,
      chave: 13,
      out: 40
    },
    lastUpdate: '5 minutos',
    location: 'Principais dados de telemetria'
  }
];

// Mock alerts data
export const mockAlerts: Alert[] = [
  {
    id: '1',
    machineId: 'itu-698',
    machineName: 'ITU - 698',
    type: 'critico',
    messages: [
      '• Tensão da bateria baixa',
      '• Tensão de alternância baixa',
      '• Pressão do óleo muito alta'
    ],
    timestamp: '2024-01-15T10:30:00Z'
  },
  {
    id: '2',
    machineId: 'itu-701',
    machineName: 'ITU - 701',
    type: 'critico',
    messages: [
      '• Tensão da bateria baixa',
      '• Tensão de alternância baixa',
      '• Pressão do óleo muito alta'
    ],
    timestamp: '2024-01-15T11:15:00Z'
  },
  {
    id: '3',
    machineId: 'itu-003',
    machineName: 'ITU - 003',
    type: 'critico',
    messages: [
      '• Tensão da bateria baixa',
      '• Tensão de alternância baixa',
      '• Pressão do óleo muito alta'
    ],
    timestamp: '2024-01-15T09:45:00Z'
  },
  {
    id: '4',
    machineId: 'itu-456',
    machineName: 'ITU - 456',
    type: 'aviso',
    messages: [
      '• Tensão da bateria baixa',
      '• Tensão de alternância baixa',
      '• Pressão do óleo muito alta'
    ],
    timestamp: '2024-01-15T08:20:00Z'
  }
];

// Mock chart data
export const mockChartData: ChartData[] = [
  { time: '00h', itu101: 65, itu102: 70, itu103: 68, itu117: 72 },
  { time: '02h', itu101: 68, itu102: 73, itu103: 71, itu117: 75 },
  { time: '04h', itu101: 70, itu102: 75, itu103: 73, itu117: 77 },
  { time: '06h', itu101: 72, itu102: 78, itu103: 75, itu117: 79 },
  { time: '08h', itu101: 75, itu102: 80, itu103: 78, itu117: 82 },
  { time: '10h', itu101: 73, itu102: 77, itu103: 76, itu117: 80 },
  { time: '12h', itu101: 71, itu102: 75, itu103: 74, itu117: 78 },
  { time: '14h', itu101: 69, itu102: 73, itu103: 72, itu117: 76 },
  { time: '16h', itu101: 67, itu102: 71, itu103: 70, itu117: 74 },
  { time: '18h', itu101: 65, itu102: 69, itu103: 68, itu117: 72 },
  { time: '20h', itu101: 63, itu102: 67, itu103: 66, itu117: 70 },
  { time: '22h', itu101: 61, itu102: 65, itu103: 64, itu117: 68 }
];

// Mock authentication functions
export const mockAuth = {
  login: async (email: string, password: string): Promise<{ success: boolean; user?: User; error?: string }> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Simple mock validation
    if (email === 'grupo03@inteli.edu.br' && password.length >= 6) {
      return { success: true, user: mockUser };
    }
    
    return { success: false, error: 'Email ou senha inválidos' };
  },
  
  logout: async (): Promise<void> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
  }
};