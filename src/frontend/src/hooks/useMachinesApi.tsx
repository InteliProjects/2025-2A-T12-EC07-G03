import { useState, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:4000/api';

// Hook para consumir dados das máquinas
export const useMachinesData = () => {
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMachines = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/machines`);
      if (!response.ok) {
        throw new Error('Falha ao carregar dados das máquinas');
      }
      const data = await response.json();
      setMachines(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Erro ao carregar máquinas:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMachines();
    
    // Atualizar dados a cada 5 segundos
    const interval = setInterval(fetchMachines, 5000);
    
    return () => clearInterval(interval);
  }, []);

  return { machines, loading, error, refetch: fetchMachines };
};

// Hook para consumir dados de uma máquina específica
export const useMachineData = (machineId) => {
  const [machine, setMachine] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMachine = async () => {
    if (!machineId) return;
    
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/machines/${machineId}`);
      if (!response.ok) {
        throw new Error('Falha ao carregar dados da máquina');
      }
      const data = await response.json();
      setMachine(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Erro ao carregar máquina:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMachine();
    
    // Atualizar dados a cada 5 segundos
    const interval = setInterval(fetchMachine, 5000);
    
    return () => clearInterval(interval);
  }, [machineId]);

  return { machine, loading, error, refetch: fetchMachine };
};

// Hook para consumir resumo do dashboard
export const useDashboardSummary = () => {
  const [summary, setSummary] = useState({
    totalOperating: 0,
    machinesDown: 0,
    activeAlerts: 0,
    upcomingMaintenance: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSummary = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/dashboard/summary`);
      if (!response.ok) {
        throw new Error('Falha ao carregar resumo do dashboard');
      }
      const data = await response.json();
      setSummary(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Erro ao carregar resumo:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
    
    // Atualizar dados a cada 10 segundos
    const interval = setInterval(fetchSummary, 10000);
    
    return () => clearInterval(interval);
  }, []);

  return { summary, loading, error, refetch: fetchSummary };
};

// Hook para status da conexão MQTT
export const useMQTTStatus = () => {
  const [status, setStatus] = useState({ connected: false, timestamp: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/mqtt/status`);
      if (!response.ok) {
        throw new Error('Falha ao carregar status MQTT');
      }
      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Erro ao carregar status MQTT:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    
    // Verificar status a cada 30 segundos
    const interval = setInterval(fetchStatus, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return { status, loading, error, refetch: fetchStatus };
};