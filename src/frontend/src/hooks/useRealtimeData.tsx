import { useState, useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

const API_BASE_URL = 'http://localhost:4000';

interface MachineData {
  id: string;
  name: string;
  status: 'operando' | 'parada' | 'manutencao' | 'desconhecido' | 'desconectado';
  telemetry: {
    rpm: number;
    bat: number;
    chave: number;
    out?: number;
    fuel_level?: number;
    oil_pressure?: number;
    coolant_temp?: number;
    vibration?: number;
    recalque?: number;
    succao?: number;
  };
  lastUpdate: string;
  location: string;
  alarms?: Array<{ message: string; timestamp: Date }>;
  events?: Array<{ message: string; timestamp: Date }>;
  statusPrediction?: {
    prediction: number;
    status: string;
    probability_normal: number;
    probability_pre_failure: number;
    risk_level: string;
    timestamp?: string;
  } | null;
}

interface DashboardSummary {
  totalOperating: number;
  machinesDown: number;
  activeAlerts: number;
  upcomingMaintenance: number;
}

interface MQTTStatus {
  connected: boolean;
  timestamp?: string;
  error?: string;
}

// Hook principal para dados em tempo real via WebSocket
export const useRealtimeData = () => {
  const [machines, setMachines] = useState<MachineData[]>([]);
  const [summary, setSummary] = useState<DashboardSummary>({
    totalOperating: 0,
    machinesDown: 0,
    activeAlerts: 0,
    upcomingMaintenance: 0
  });
  const [mqttStatus, setMqttStatus] = useState<MQTTStatus>({ connected: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Criar conexão WebSocket
    socketRef.current = io(API_BASE_URL, {
      transports: ['websocket', 'polling'],
      timeout: 20000,
    });

    const socket = socketRef.current;

    // Event listeners
    socket.on('connect', () => {
      setConnected(true);
      setError(null);
    });

    socket.on('disconnect', () => {
      setConnected(false);
    });

    socket.on('connect_error', (err) => {
      setError(`Erro de conexão WebSocket: ${err.message}`);
      setConnected(false);
    });

    // Receber dados iniciais
    socket.on('initialData', (data) => {
      setMachines(data.machines || []);
      setSummary(data.summary || {
        totalOperating: 0,
        machinesDown: 0,
        activeAlerts: 0,
        upcomingMaintenance: 0
      });
      setMqttStatus(data.mqttStatus || { connected: false });
      setLoading(false);
    });

    // Receber atualizações de máquinas em tempo real
    socket.on('machineUpdate', (update) => {
      setMachines(prevMachines => {
        const newMachines = [...prevMachines];
        const index = newMachines.findIndex(m => m.id === update.machineId);
        
        if (index >= 0) {
          newMachines[index] = update.data;
        } else {
          newMachines.push(update.data);
        }
        
        return newMachines;
      });
    });

    // Receber atualizações do resumo em tempo real
    socket.on('summaryUpdate', (newSummary) => {
      setSummary(newSummary);
    });

    // Receber atualizações do status MQTT
    socket.on('mqttStatus', (status) => {
      setMqttStatus({
        ...status,
        timestamp: new Date().toISOString()
      });
    });

    // Cleanup na desmontagem
    return () => {
      socket.disconnect();
    };
  }, []);

  // Função para reconectar manualmente
  const reconnect = () => {
    if (socketRef.current) {
      socketRef.current.connect();
    }
  };

  return {
    machines,
    summary,
    mqttStatus,
    loading,
    error,
    connected,
    reconnect
  };
};

// Hook para uma máquina específica (opcional, para compatibilidade)
export const useMachineData = (machineId: string) => {
  const { machines, loading, error } = useRealtimeData();
  
  const machine = machines.find(m => m.id === machineId) || null;
  
  return { machine, loading, error };
};

// Hooks individuais para compatibilidade com código existente
export const useMachinesData = () => {
  const { machines, loading, error } = useRealtimeData();
  
  const refetch = () => {
    // No refetch needed - data is real-time
  };
  
  return { machines, loading, error, refetch };
};

export const useDashboardSummary = () => {
  const { summary, loading, error } = useRealtimeData();
  
  const refetch = () => {
    // No refetch needed - data is real-time
  };
  
  return { summary, loading, error, refetch };
};

export const useMQTTStatus = () => {
  const { mqttStatus, loading, error } = useRealtimeData();
  
  const refetch = () => {
    // No refetch needed - data is real-time
  };
  
  return { status: mqttStatus, loading, error, refetch };
};