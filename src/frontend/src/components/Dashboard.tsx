import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Legend, LabelList } from 'recharts';
import { User, AlertTriangle, LogOut, PieChart, Bot, Gauge, Battery, Zap, Wrench, Wifi, WifiOff, Search, Shield, ShieldAlert } from 'lucide-react';
import { MachineModal } from '@/components/MachineModal';
import { useRealtimeData } from '@/hooks/useRealtimeData';
import api from '@/lib/api';
import {
  mockAlerts,
  mockChartData,
  mockUser,
  type User as UserType
} from '@/data/mockData';

interface DashboardProps {
  user?: UserType;
  onLogout?: () => void;
}

interface HealthPredictionDetailed {
  id?: string;
  timestamp: string;
  motor_pump: string;
  status: {
    hidraulico: string;
    lubrificacao: string;
  };
  indices: {
    hidraulico: number;
    lubrificacao: number;
  };
  success: boolean;
}

interface HealthPredictionGeneral {
  id: string;
  timestamp: string;
  motor_pump: string;
  meta: {
    machine: string;
    n_outputs: number;
    timesteps: number;
    n_features: number;
    fetched_rows: number;
    feature_order: string[];
    requested_time_steps: number;
  };
  status: {
    saude_geral: string;
  };
  indices: {
    saude_geral: number;
  };
  success: boolean;
}

type HealthPrediction = HealthPredictionDetailed | HealthPredictionGeneral;

interface MachineData {
  id: string;
  name: string;
  status: 'operando' | 'parada' | 'manutencao' | 'desconhecido' | 'desconectado';
  telemetry: {
    // Engine data
    rpm?: number;
    bat?: number;
    chave?: number;
    fuel_level?: number;
    fuel_consumption?: number;
    oil_pressure?: number;
    oil_level?: number;
    coolant_temp?: number;
    engine_runtime_hours?: number;
    starts_number?: number;

    // Pump data
    recalque?: number;
    succao?: number;
    vibration?: number;

    // LED status
    led_auto?: number;
    led_manual?: number;
    led_stop?: number;

    // Location
    latitude?: number;
    longitude?: number;

    // Deprecated/compatibility
    out?: number;
  };
  lastUpdate: string;
  location: string;
  alarms?: Array<{ message: string; timestamp: Date }>;
  events?: Array<{ message: string; timestamp: Date }>;
  statusPrediction?: {
    prediction: number; // 0 = normal, 1 = pré-falha
    status: string;
    probability_normal: number;
    probability_pre_failure: number;
    risk_level: string;
    timestamp?: string;
  } | null;
}

export const Dashboard: React.FC<DashboardProps> = ({
  user = mockUser,
  onLogout
}) => {
  const navigate = useNavigate();
  const [selectedMachine, setSelectedMachine] = useState<MachineData | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [machinesWithPredictions, setMachinesWithPredictions] = useState<MachineData[]>([]);
  const [healthPredictions, setHealthPredictions] = useState<HealthPrediction[]>([]);
  const [loadingHealthData, setLoadingHealthData] = useState(false);
  const predictionIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const healthPredictionIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Hook para dados em tempo real via WebSocket
  const {
    machines,
    summary,
    mqttStatus,
    loading,
    error,
    connected: wsConnected,
    reconnect
  } = useRealtimeData();

  // Função para verificar se é predição detalhada (com hidraulico e lubrificacao)
  const isDetailedPrediction = (pred: HealthPrediction): pred is HealthPredictionDetailed => {
    return 'hidraulico' in (pred as any).indices;
  };

  // Função para verificar se é predição geral (com saude_geral)
  const isGeneralPrediction = (pred: HealthPrediction): pred is HealthPredictionGeneral => {
    return 'saude_geral' in (pred as any).indices;
  };

  // Função para buscar predições de funcionamento para todas as máquinas
  const fetchStatusPredictions = async () => {
    if (machines.length === 0) return;

    try {
      const predictionsPromises = machines.map(async (machine) => {
        try {
          const response = await api.get(`/api/data/machines/${machine.name}/status-prediction`);
          return {
            machineName: machine.name,
            prediction: response.data.prediction
          };
        } catch (error) {
          console.error(`Erro ao buscar predição para ${machine.name}:`, error);
          return {
            machineName: machine.name,
            prediction: null
          };
        }
      });

      const predictions = await Promise.all(predictionsPromises);

      // Atualizar máquinas com predições
      const updatedMachines = machines.map(machine => {
        const pred = predictions.find(p => p.machineName === machine.name);
        return {
          ...machine,
          statusPrediction: pred?.prediction || null
        };
      });

      setMachinesWithPredictions(updatedMachines);
    } catch (error) {
      console.error('Erro ao buscar predições:', error);
    }
  };

  // Função para buscar predições de saúde (health) para todas as máquinas
  const fetchHealthPredictions = async () => {
    if (machines.length === 0) return;

    setLoadingHealthData(true);
    try {
      // Tentar buscar dados reais da API
      const healthPromises = machines.map(async (machine) => {
        try {
          const response = await api.get(`/api/data/machines/${machine.name}/health-prediction`);
          if (response.data.success && response.data.prediction) {
            return response.data.prediction;
          }
          return null;
        } catch (error) {
          console.error(`Erro ao buscar predição de saúde para ${machine.name}:`, error);
          return null;
        }
      });

      const predictions = await Promise.all(healthPromises);
      const validPredictions = predictions.filter(p => p !== null) as HealthPrediction[];

      // Ordenar por melhor saúde
      validPredictions.sort((a, b) => {
        let avgA = 0;
        let avgB = 0;

        if (isDetailedPrediction(a)) {
          avgA = ((a.indices?.hidraulico ?? 0) + (a.indices?.lubrificacao ?? 0)) / 2;
        } else if (isGeneralPrediction(a)) {
          avgA = a.indices?.saude_geral ?? 0;
        }

        if (isDetailedPrediction(b)) {
          avgB = ((b.indices?.hidraulico ?? 0) + (b.indices?.lubrificacao ?? 0)) / 2;
        } else if (isGeneralPrediction(b)) {
          avgB = b.indices?.saude_geral ?? 0;
        }

        return avgB - avgA;
      });

      setHealthPredictions(validPredictions);
    } catch (error) {
      console.error('Erro ao buscar predições de saúde:', error);
    } finally {
      setLoadingHealthData(false);
    }
  };

  // Buscar predições quando as máquinas mudarem
  useEffect(() => {
    if (machines.length > 0) {
      fetchStatusPredictions();
      fetchHealthPredictions();
    }
  }, [machines.length]); // Só re-executa quando o número de máquinas muda

  // Atualizar predições a cada 60 segundos
  useEffect(() => {
    predictionIntervalRef.current = setInterval(() => {
      fetchStatusPredictions();
    }, 60000); // 60 segundos

    return () => {
      if (predictionIntervalRef.current) {
        clearInterval(predictionIntervalRef.current);
      }
    };
  }, [machines]);

  // Atualizar predições de saúde a cada 60 segundos
  useEffect(() => {
    healthPredictionIntervalRef.current = setInterval(() => {
      fetchHealthPredictions();
    }, 60000); // 60 segundos

    return () => {
      if (healthPredictionIntervalRef.current) {
        clearInterval(healthPredictionIntervalRef.current);
      }
    };
  }, [machines]);

  // Usar máquinas com predições ou máquinas normais se ainda não tiver predições
  const displayMachines = machinesWithPredictions.length > 0 ? machinesWithPredictions : machines;

  // Filtrar máquinas baseado no termo de pesquisa
  const filteredMachines = displayMachines.filter(machine =>
    machine.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    machine.location.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Preparar dados para o gráfico de saúde
  const healthChartData = healthPredictions.map(pred => {
    if (isDetailedPrediction(pred)) {
      return {
        name: pred.motor_pump ?? 'Desconhecido',
        hidraulico: pred.indices?.hidraulico ?? 0,
        lubrificacao: pred.indices?.lubrificacao ?? 0,
        statusHidraulico: pred.status?.hidraulico ?? 'DESCONHECIDO',
        statusLubrificacao: pred.status?.lubrificacao ?? 'DESCONHECIDO',
        type: 'detailed' as const
      };
    } else if (isGeneralPrediction(pred)) {
      return {
        name: pred.motor_pump ?? 'Desconhecido',
        saude_geral: pred.indices?.saude_geral ?? 0,
        statusGeral: pred.status?.saude_geral ?? 'DESCONHECIDO',
        type: 'general' as const
      };
    }
    return null;
  }).filter(item => item !== null);

  // Preparar alertas críticos baseados em indicadores de saúde abaixo de 50%
  const criticalAlerts = healthPredictions
    .map(pred => {
      const alerts: string[] = [];
      
      if (isDetailedPrediction(pred)) {
        const hid = pred.indices?.hidraulico ?? 0;
        const lub = pred.indices?.lubrificacao ?? 0;
        const statusH = pred.status?.hidraulico ?? 'DESCONHECIDO';
        const statusL = pred.status?.lubrificacao ?? 'DESCONHECIDO';
        
        if (hid < 50) {
          alerts.push(`Sistema Hidráulico: ${hid.toFixed(1)}% (${statusH})`);
        }
        if (lub < 50) {
          alerts.push(`Sistema de Lubrificação: ${lub.toFixed(1)}% (${statusL})`);
        }
      } else if (isGeneralPrediction(pred)) {
        const saude = pred.indices?.saude_geral ?? 0;
        const status = pred.status?.saude_geral ?? 'DESCONHECIDO';
        
        if (saude < 50) {
          alerts.push(`Saúde Geral: ${saude.toFixed(1)}% (${status})`);
        }
      }
      
      return {
        machineName: pred.motor_pump,
        alerts,
        timestamp: pred.timestamp
      };
    })
    .filter(alert => alert.alerts.length > 0);

  // Função para formatar valores - mostra "--" quando não há dados válidos
  const formatValue = (value: number | undefined, unit: string = '', decimals: number = 0): string => {
    // Se undefined ou null = não recebeu dados = mostra "--"
    if (value === undefined || value === null) {
      return '--';
    }
    // Se zero ou qualquer número válido = mostra o valor
    return `${value.toFixed(decimals)}${unit}`;
  };

  const handleLogout = () => {
    onLogout?.();
  };

  const handleMachineClick = (machine: MachineData) => {
    setSelectedMachine(machine);
    setIsModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <img
              src="https://api.builder.io/api/v1/image/assets/TEMP/b05acf8f3d60338dd8fd8c1bf4ee6127c37449b6?width=186"
              alt="Flow Solutions Logo"
              className="w-10 h-10 rounded-full"
            />
            <h1 className="text-xl font-bold text-[#151D48]">Flow Solutions</h1>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <img
                src={user.avatar}
                alt="User Avatar"
                className="w-10 h-10 rounded-full"
              />
              <span className="text-gray-700 font-medium">{user.name}</span>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 text-gray-500 hover:text-red-600 transition-colors"
              title="Sair"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="group w-20 hover:w-64 bg-white shadow-sm min-h-screen transition-all duration-300 overflow-hidden">
          <nav className="p-4 space-y-2">
            <button className="w-full h-12 flex items-center px-2 py-3 bg-[#1934A5] text-white rounded-lg font-medium relative">
              <div className="w-full flex justify-center group-hover:justify-start group-hover:pl-2 transition-all duration-300">
                <PieChart className="w-4 h-4 min-w-[1rem]" />
              </div>
              <span className="absolute left-10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap">
                Dashboard
              </span>
            </button>
            <button
              onClick={() => navigate('/models')}
              className="w-full h-12 flex items-center px-2 py-3 text-gray-600 hover:bg-gray-50 rounded-lg relative"
            >
              <div className="w-full flex justify-center group-hover:justify-start group-hover:pl-2 transition-all duration-300">
                <Bot className="w-4 h-4 min-w-[1rem]" />
              </div>
              <span className="absolute left-10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap">
                Modelos
              </span>
            </button>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          {/* Dashboard Title */}
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Dashboard</h2>

          {/* Summary Cards - HOJE */}
          <div className="mb-6">
            <div className="bg-[#1934A5] rounded-xl p-6 text-white">
              <h3 className="text-xl font-bold mb-4">HOJE</h3>
              <p className="text-sm opacity-90 mb-4">Resumo das Máquinas</p>

              <div className="grid grid-cols-4 gap-4">
                <div className="bg-green-500 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold mb-2">
                    {loading ? '...' : summary.totalOperating}
                  </div>
                  <div className="text-sm">Total Operando</div>
                </div>

                <div className="bg-gray-400 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold mb-2">
                    {loading ? '...' : summary.machinesDown}
                  </div>
                  <div className="text-sm">Máquinas paradas</div>
                </div>

                <div className="bg-red-500 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold mb-2">
                    {loading || loadingHealthData ? '...' : criticalAlerts.length}
                  </div>
                  <div className="text-sm">Alertas Ativos</div>
                </div>

                <div className="bg-white text-gray-800 rounded-lg p-4 text-center">
                  <div className="text-3xl font-bold mb-2">
                    {loading ? '...' : summary.upcomingMaintenance}
                  </div>
                  <div className="text-sm">Próx. Manutenção</div>
                </div>
              </div>
            </div>
          </div>

          {/* Health Indicators Chart */}
          <div className="mb-6">
            <div className="bg-white rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">
                Indicadores de Saúde das Máquinas
              </h3>
              {loadingHealthData ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-gray-500">Carregando dados de saúde...</div>
                </div>
              ) : healthChartData.length === 0 ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-gray-500">Nenhum dado de saúde disponível</div>
                </div>
              ) : (
                <div style={{ width: '100%', height: 400 }}>
                  <ResponsiveContainer>
                    <BarChart
                      data={healthChartData}
                      margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                    >
                      <XAxis
                        dataKey="name"
                        angle={-45}
                        textAnchor="end"
                        height={80}
                        tick={{ fontSize: 12, fill: '#6b7280' }}
                      />
                      <YAxis
                        domain={[0, 100]}
                        tick={{ fontSize: 12, fill: '#6b7280' }}
                        label={{ value: 'Índice de Saúde (%)', angle: -90, position: 'insideLeft', style: { fontSize: 12, fill: '#6b7280' } }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'white',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                        formatter={(value: number, name: string, props: any) => {
                          if (props.payload.type === 'detailed') {
                            const status = name === 'hidraulico'
                              ? props.payload.statusHidraulico
                              : props.payload.statusLubrificacao;
                            return [`${value.toFixed(1)}% (${status})`, name === 'hidraulico' ? 'Hidráulico' : 'Lubrificação'];
                          } else {
                            return [`${value.toFixed(1)}% (${props.payload.statusGeral})`, 'Saúde Geral'];
                          }
                        }}
                      />
                      <Legend
                        wrapperStyle={{ paddingTop: '20px' }}
                        formatter={(value) => {
                          if (value === 'hidraulico') return 'Hidráulico';
                          if (value === 'lubrificacao') return 'Lubrificação';
                          if (value === 'saude_geral') return 'Saúde Geral';
                          return value;
                        }}
                      />
                      <Bar
                        dataKey="hidraulico"
                        name="hidraulico"
                        fill="#10b981"
                        radius={[8, 8, 0, 0]}
                      >
                        <LabelList
                          dataKey="hidraulico"
                          position="top"
                          formatter={(value: number) => value ? `${value.toFixed(1)}%` : ''}
                          style={{ fontSize: '11px', fontWeight: 'bold', fill: '#374151' }}
                        />
                      </Bar>
                      <Bar
                        dataKey="lubrificacao"
                        name="lubrificacao"
                        fill="#8b5cf6"
                        radius={[8, 8, 0, 0]}
                      >
                        <LabelList
                          dataKey="lubrificacao"
                          position="top"
                          formatter={(value: number) => value ? `${value.toFixed(1)}%` : ''}
                          style={{ fontSize: '11px', fontWeight: 'bold', fill: '#374151' }}
                        />
                      </Bar>
                      <Bar
                        dataKey="saude_geral"
                        name="saude_geral"
                        fill="#3b82f6"
                        radius={[8, 8, 0, 0]}
                      >
                        <LabelList
                          dataKey="saude_geral"
                          position="top"
                          formatter={(value: number) => value ? `${value.toFixed(1)}%` : ''}
                          style={{ fontSize: '11px', fontWeight: 'bold', fill: '#374151' }}
                        />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>

          {/* Critical Alerts */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <h3 className="text-lg font-semibold text-gray-800">Alertas Críticos de Saúde</h3>
              <span className="text-sm text-gray-500">
                (Indicadores abaixo de 50%)
              </span>
            </div>

            {criticalAlerts.length === 0 ? (
              <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 text-center">
                <p className="text-gray-500">Nenhum alerta crítico no momento</p>
                <p className="text-sm text-gray-400 mt-1">Todos os indicadores de saúde estão acima de 50%</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                {criticalAlerts.map((alert, index) => (
                  <div key={`${alert.machineName}-${index}`} className="bg-white rounded-lg p-4 shadow-sm border border-red-200">
                    <div className="flex items-center gap-2 mb-3">
                      <AlertTriangle className="w-4 h-4 text-red-500" />
                      <span className="font-semibold text-gray-800">{alert.machineName}</span>
                    </div>

                    <div className="space-y-1 text-sm text-gray-600">
                      {alert.alerts.map((message, msgIndex) => (
                        <div key={msgIndex} className="flex items-start gap-2">
                          <AlertTriangle className="w-3 h-3 text-red-500 mt-0.5 flex-shrink-0" />
                          <span>{message}</span>
                        </div>
                      ))}
                    </div>

                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <p className="text-xs text-gray-400">
                        Última atualização: {new Date(alert.timestamp).toLocaleString('pt-BR')}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Status das Conexões */}
          <div className="mb-4 flex gap-2">
            <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${wsConnected
                ? 'bg-blue-100 text-blue-800'
                : 'bg-red-100 text-red-800'
              }`}>
              {wsConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
              {wsConnected ? 'WebSocket Conectado' : 'WebSocket Desconectado'}
            </div>

            <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${mqttStatus.connected
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
              }`}>
              {mqttStatus.connected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
              {loading ? 'Verificando...' : mqttStatus.connected ? 'MQTT Conectado' : 'MQTT Desconectado'}
            </div>

            {!wsConnected && (
              <button
                onClick={reconnect}
                className="px-3 py-1 bg-blue-500 text-white rounded-full text-sm hover:bg-blue-600"
              >
                Reconectar
              </button>
            )}
          </div>

          {/* Barra de Pesquisa */}
          <div className="mb-6">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Pesquisar por nome ou localização da bomba..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              )}
            </div>
            {searchTerm && (
              <p className="mt-2 text-sm text-gray-600">
                Mostrando {filteredMachines.length} de {machines.length} máquinas
              </p>
            )}
          </div>

          {/* Machine Status Cards */}
          <div className="group-hover:grid-cols-3 grid grid-cols-4 gap-4">
            {loading ? (
              <div className="col-span-4 text-center py-8 text-gray-500">
                Carregando dados das máquinas...
              </div>
            ) : error ? (
              <div className="col-span-4 text-center py-8 text-red-500">
                Erro ao carregar dados: {error}
              </div>
            ) : filteredMachines.length === 0 ? (
              <div className="col-span-4 text-center py-8 text-gray-500">
                {searchTerm ? `Nenhuma máquina encontrada para "${searchTerm}"` : 'Nenhuma máquina encontrada'}
              </div>
            ) : (
              filteredMachines.map((machine) => (
                <div
                  key={machine.id}
                  className="bg-white rounded-lg p-4 shadow-sm border cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => handleMachineClick(machine)}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex flex-col gap-1">
                      <h4 className="font-bold text-gray-800">{machine.name}</h4>
                      {/* Status de conexão MQTT */}
                      <div className="flex items-center gap-1">
                        {machine.status !== 'desconectado' ? (
                          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-green-50 text-green-700 border border-green-200">
                            <Wifi className="w-3 h-3" />
                            <span>Conectado</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-red-50 text-red-700 border border-red-200">
                            <WifiOff className="w-3 h-3" />
                            <span>Desconectado</span>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${machine.status === 'operando' ? 'bg-green-100 text-green-800' :
                        machine.status === 'parada' ? 'bg-gray-100 text-gray-800' :
                          machine.status === 'manutencao' ? 'bg-yellow-100 text-yellow-800' :
                            machine.status === 'desconectado' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                      }`}>
                      {machine.status}
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mb-3">{machine.location}</p>

                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <Gauge className="w-4 h-4 text-gray-500" />
                      <span className="text-gray-600">MOTOR:</span>
                      <span className="font-medium">{formatValue(machine.telemetry.rpm, ' rpm', 1)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Wrench className="w-4 h-4 text-gray-500" />
                      <span className="text-gray-600">ÓLEO:</span>
                      <span className="font-medium">{formatValue(machine.telemetry.oil_pressure, ' mca', 1)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Battery className="w-4 h-4 text-gray-500" />
                      <span className="text-gray-600">BATERIA:</span>
                      <span className="font-medium">{formatValue(machine.telemetry.bat, 'V', 1)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-gray-500" />
                      <span className="text-gray-600">ALTERNADOR:</span>
                      <span className="font-medium">{formatValue(machine.telemetry.chave, 'V', 1)}</span>
                    </div>
                  </div>

                  {/* Indicador de Pré-Falha */}
                  {machine.statusPrediction && (
                    <div className={`mt-3 p-2 rounded-lg border ${machine.statusPrediction.prediction === 1
                        ? 'bg-red-50 border-red-200'
                        : 'bg-green-50 border-green-200'
                      }`}>
                      <div className="flex items-center gap-2">
                        {machine.statusPrediction.prediction === 1 ? (
                          <ShieldAlert className="w-4 h-4 text-red-600" />
                        ) : (
                          <Shield className="w-4 h-4 text-green-600" />
                        )}
                        <div className="flex-1">
                          <div className={`text-xs font-semibold ${machine.statusPrediction.prediction === 1
                              ? 'text-red-700'
                              : 'text-green-700'
                            }`}>
                            {machine.statusPrediction.status}
                          </div>
                          <div className="text-xs text-gray-600 mt-0.5">
                            {machine.statusPrediction.prediction === 1 ? (
                              <>
                                Risco: {machine.statusPrediction.risk_level} ({(machine.statusPrediction.probability_pre_failure * 100).toFixed(1)}%)
                              </>
                            ) : (
                              <>
                                Normal: {(machine.statusPrediction.probability_normal * 100).toFixed(1)}%
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex items-center justify-between mt-3 pt-3 border-t">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${machine.status === 'desconectado' ? 'bg-red-500' : 'bg-green-500'
                        } ${machine.status !== 'desconectado' ? 'animate-pulse' : ''}`}></div>
                      <span className="text-xs text-gray-500">
                        {machine.status === 'desconectado' ? 'Sem dados' : 'Dados MQTT'}
                      </span>
                    </div>
                    <span className="text-xs text-gray-400" title="Última atualização via MQTT">
                      {machine.lastUpdate}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </main>
      </div>

      <MachineModal
        machine={selectedMachine}
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
};