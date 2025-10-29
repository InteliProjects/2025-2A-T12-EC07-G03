import React, { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { X, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import api from '@/lib/api';

interface HealthPredictionDetailed {
  indices: {
    hidraulico: number;
    lubrificacao: number;
  };
  status: {
    hidraulico: string;
    lubrificacao: string;
  };
  timestamp: string;
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
}

interface MachineModalProps {
  machine: MachineData | null;
  open: boolean;
  onClose: () => void;
}

interface GRUModel {
  id: string;
  machine_name: string;
  bucket_address: string;
  data_start_date: string;
  data_end_date: string;
  created_at: string;
  model_type: string;
  metrics?: any;
}

export const MachineModal: React.FC<MachineModalProps> = ({ machine, open, onClose }) => {
  const [healthPrediction, setHealthPrediction] = useState<HealthPrediction | null>(null);
  const [loadingPrediction, setLoadingPrediction] = useState(false);
  const [gruModels, setGruModels] = useState<GRUModel[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [selectedHorizon, setSelectedHorizon] = useState<number>(60);
  const [predictionStatus, setPredictionStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });

  // Buscar predição de saúde e modelos GRU quando o modal abre
  useEffect(() => {
    if (open && machine) {
      fetchHealthPrediction();
      fetchGRUModels();
      // Limpar status de predição anterior
      setPredictionStatus({ type: null, message: '' });
    }
  }, [open, machine]);

  const fetchHealthPrediction = async () => {
    if (!machine) return;
    
    setLoadingPrediction(true);
    try {
      console.log("Buscando predição de saúde para", machine.name);
      const response = await api.get(`/api/data/machines/${machine.name}/health-prediction`);
      console.log("Resposta da predição DE SAUDEEEEEE:", response.data);
      if (response.data.success && response.data.prediction) {
        setHealthPrediction(response.data.prediction);
      } else {
        setHealthPrediction(null);
      }
    } catch (error) {
      console.error('Erro ao buscar predição de saúde:', error);
      setHealthPrediction(null);
    } finally {
      setLoadingPrediction(false);
    }
  };

  const fetchGRUModels = async () => {
    if (!machine) return;
    
    try {
      const response = await api.get(`/api/models/gru/${machine.name}`);
      if (response.data.success && response.data.models) {
        setGruModels(response.data.models);
        // Selecionar o primeiro modelo por padrão
        if (response.data.models.length > 0) {
          setSelectedModelId(response.data.models[0].id);
        }
      }
    } catch (error) {
      console.error('Erro ao buscar modelos GRU:', error);
      setGruModels([]);
    }
  };

  const handlePrediction = async () => {
    if (!machine || !selectedModelId || !selectedHorizon) {
      setPredictionStatus({
        type: 'error',
        message: 'Por favor, selecione um modelo e um horizonte de previsão'
      });
      return;
    }

    // Encontrar o modelo selecionado para pegar o bucket_address
    const selectedModel = gruModels.find(model => model.id === selectedModelId);
    if (!selectedModel) {
      setPredictionStatus({
        type: 'error',
        message: 'Modelo selecionado não encontrado'
      });
      return;
    }

    setLoadingPrediction(true);
    setPredictionStatus({ type: null, message: '' });

    try {
      console.log('Enviando requisição de predição:', {
        machine_name: machine.name,
        model_bucket_address: selectedModel.bucket_address,
        time_steps: selectedHorizon
      });

      const response = await api.post('/model-inference/machine/gru/predict', {
        machine_name: machine.name,
        model_bucket_address: selectedModel.bucket_address,
        time_steps: selectedHorizon
      });

      console.log('Resposta da predição:', response.data);

      if (response.data.success) {
        // Atualizar a predição de saúde com a nova resposta
        const newPrediction: HealthPredictionGeneral = {
          id: `pred-${Date.now()}`,
          timestamp: new Date().toISOString(),
          motor_pump: machine.name,
          meta: response.data.meta,
          status: response.data.status,
          indices: response.data.indices,
          success: true
        };

        setHealthPrediction(newPrediction);
        
        setPredictionStatus({
          type: 'success',
          message: `Predição realizada com sucesso! Índice de saúde: ${response.data.indices.saude_geral.toFixed(1)}% (${response.data.status.saude_geral})`
        });

        // Atualizar também a predição do backend (caso seja salva lá)
        await fetchHealthPrediction();
      } else {
        setPredictionStatus({
          type: 'error',
          message: 'Erro ao realizar predição. Tente novamente.'
        });
      }
    } catch (error: any) {
      console.error('Erro ao realizar predição:', error);
      setPredictionStatus({
        type: 'error',
        message: error.response?.data?.error || 'Erro ao realizar predição. Verifique se há dados suficientes disponíveis.'
      });
    } finally {
      setLoadingPrediction(false);
    }
  };

  if (!machine) return null;

  // Função para verificar se é predição detalhada (com hidraulico e lubrificacao)
  const isDetailedPrediction = (pred: HealthPrediction): pred is HealthPredictionDetailed => {
    return 'hidraulico' in (pred as any).indices;
  };

  // Função para verificar se é predição geral (com saude_geral)
  const isGeneralPrediction = (pred: HealthPrediction): pred is HealthPredictionGeneral => {
    return 'saude_geral' in (pred as any).indices;
  };

  // Função para formatar valores - mostra "--" quando não há dados válidos
  const formatValue = (value: number | undefined, unit: string = '', decimals: number = 0): string => {
    // Se undefined ou null = não recebeu dados = mostra "--"
    if (value === undefined || value === null) {
      return '--';
    }
    // Se zero ou qualquer número válido = mostra o valor
    return `${value.toFixed(decimals)}${unit}`;
  };

  // Função para obter cor do status
  const getStatusColor = (status: string): string => {
    switch (status?.toUpperCase()) {
      case 'NORMAL':
        return '#10b981'; // green
      case 'ATENÇÃO':
        return '#f59e0b'; // orange
      case 'ALERTA':
        return '#ef4444'; // red
      default:
        return '#6b7280'; // gray
    }
  };

  // Verificar se os dados de predição são válidos
  const hasValidPrediction = healthPrediction && (
    (isDetailedPrediction(healthPrediction) && 
      healthPrediction.indices && 
      healthPrediction.status &&
      typeof healthPrediction.indices.hidraulico === 'number' &&
      typeof healthPrediction.indices.lubrificacao === 'number') ||
    (isGeneralPrediction(healthPrediction) &&
      healthPrediction.indices &&
      healthPrediction.status &&
      typeof healthPrediction.indices.saude_geral === 'number')
  );

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl p-6 max-h-[80vh] overflow-y-auto">
        <DialogHeader className="flex flex-row items-center justify-between">
          <DialogTitle className="text-2xl font-bold text-gray-800">{machine.name}</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Status */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Estado:</span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                machine.status === 'operando' ? 'bg-green-100 text-green-800' :
                machine.status === 'parada' ? 'bg-red-100 text-red-800' :
                machine.status === 'manutencao' ? 'bg-yellow-100 text-yellow-800' :
                machine.status === 'desconectado' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {machine.status === 'operando' ? 'Normal' :
                 machine.status === 'parada' ? 'Parada' :
                 machine.status === 'manutencao' ? 'Manutenção' :
                 machine.status === 'desconectado' ? 'Desconectado' : 
                 'Desconhecido'}
              </span>
            </div>
            
            {/* Status de Conexão MQTT */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">MQTT:</span>
              {machine.status !== 'desconectado' ? (
                <div className="flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-green-50 text-green-700 border border-green-200">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                  <span>Conectado</span>
                </div>
              ) : (
                <div className="flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-red-50 text-red-700 border border-red-200">
                  <div className="w-2 h-2 rounded-full bg-red-500"></div>
                  <span>Desconectado</span>
                </div>
              )}
            </div>
          </div>

          {/* Health Indicators */}
          {loadingPrediction && !predictionStatus.type ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
              <span className="ml-2 text-gray-600">Carregando predições...</span>
            </div>
          ) : hasValidPrediction ? (
            <div>
              {/* Renderizar predição detalhada (hidraulico e lubrificacao) */}
              {isDetailedPrediction(healthPrediction) && (
                <>
                  <div className="grid grid-cols-2 gap-8 mb-4">
                    {/* Indicador Hidráulico */}
                    <div className="text-center">
                      <div className="relative w-24 h-24 mx-auto mb-2">
                        <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
                          <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="#e5e7eb"
                            strokeWidth="2"
                          />
                          <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke={getStatusColor(healthPrediction.status.hidraulico)}
                            strokeWidth="2"
                            strokeDasharray={`${healthPrediction.indices.hidraulico}, 100`}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center flex-col">
                          <span className="text-lg font-bold text-gray-800">
                            {healthPrediction.indices.hidraulico.toFixed(1)}%
                          </span>
                          <span 
                            className="text-[10px] font-medium mt-0.5"
                            style={{ color: getStatusColor(healthPrediction.status.hidraulico) }}
                          >
                            {healthPrediction.status.hidraulico}
                          </span>
                        </div>
                      </div>
                      <p className="text-xs text-gray-600">
                        Índice de saúde do<br />subsistema hidráulico
                      </p>
                    </div>

                    {/* Indicador Lubrificação */}
                    <div className="text-center">
                      <div className="relative w-24 h-24 mx-auto mb-2">
                        <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
                          <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="#e5e7eb"
                            strokeWidth="2"
                          />
                          <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke={getStatusColor(healthPrediction.status.lubrificacao)}
                            strokeWidth="2"
                            strokeDasharray={`${healthPrediction.indices.lubrificacao}, 100`}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center flex-col">
                          <span className="text-lg font-bold text-gray-800">
                            {healthPrediction.indices.lubrificacao.toFixed(1)}%
                          </span>
                          <span 
                            className="text-[10px] font-medium mt-0.5"
                            style={{ color: getStatusColor(healthPrediction.status.lubrificacao) }}
                          >
                            {healthPrediction.status.lubrificacao}
                          </span>
                        </div>
                      </div>
                      <p className="text-xs text-gray-600">
                        Índice de saúde do<br />subsistema de lubrificação
                      </p>
                    </div>
                  </div>
                  
                  {/* Timestamp da predição */}
                  <div className="text-center text-xs text-gray-500">
                    Última predição: {new Date(healthPrediction.timestamp).toLocaleString('pt-BR')}
                  </div>
                </>
              )}

              {/* Renderizar predição geral (saude_geral) */}
              {isGeneralPrediction(healthPrediction) && (
                <>
                  <div className="flex justify-center mb-4">
                    {/* Indicador de Saúde Geral */}
                    <div className="text-center">
                      <div className="relative w-32 h-32 mx-auto mb-2">
                        <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 36 36">
                          <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="#e5e7eb"
                            strokeWidth="2"
                          />
                          <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke={getStatusColor(healthPrediction.status.saude_geral)}
                            strokeWidth="2"
                            strokeDasharray={`${healthPrediction.indices.saude_geral}, 100`}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center flex-col">
                          <span className="text-2xl font-bold text-gray-800">
                            {healthPrediction.indices.saude_geral.toFixed(1)}%
                          </span>
                          <span 
                            className="text-xs font-medium mt-1"
                            style={{ color: getStatusColor(healthPrediction.status.saude_geral) }}
                          >
                            {healthPrediction.status.saude_geral}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 font-medium">
                        Índice de Saúde Geral
                      </p>
                    </div>
                  </div>
                  
                  {/* Informações adicionais da predição */}
                  <div className="text-center space-y-1">
                    <div className="text-xs text-gray-500">
                      Última predição: {new Date(healthPrediction.timestamp).toLocaleString('pt-BR')}
                    </div>
                    {healthPrediction.meta && (
                      <div className="text-xs text-gray-400">
                        Timesteps: {healthPrediction.meta.timesteps} | Features: {healthPrediction.meta.n_features} | Dados: {healthPrediction.meta.fetched_rows} linhas
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p className="text-sm">Nenhuma predição de saúde disponível para esta máquina</p>
              <p className="text-xs mt-2">Realize uma nova predição abaixo</p>
            </div>
          )}

          {/* Health Prediction Section */}
          <div className="border-t pt-6">
            <h3 className="font-medium text-gray-800 mb-4">
              Realizar nova previsão de indicadores de saúde
            </h3>
            
            {/* Status da predição */}
            {predictionStatus.type && (
              <div className={`mb-4 p-3 rounded-lg flex items-start gap-2 ${
                predictionStatus.type === 'success' 
                  ? 'bg-green-50 border border-green-200' 
                  : 'bg-red-50 border border-red-200'
              }`}>
                {predictionStatus.type === 'success' ? (
                  <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                )}
                <p className={`text-sm ${
                  predictionStatus.type === 'success' ? 'text-green-800' : 'text-red-800'
                }`}>
                  {predictionStatus.message}
                </p>
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Horizonte de Previsão (timesteps)
                </label>
                <select 
                  className="w-full p-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={selectedHorizon}
                  onChange={(e) => setSelectedHorizon(Number(e.target.value))}
                  disabled={loadingPrediction}
                >
                  <option value="">Selecione o horizonte</option>
                  <option value="60">60 timesteps</option>
                  <option value="120">120 timesteps</option>
                  <option value="180">180 timesteps</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Modelo GRU
                </label>
                <select 
                  className="w-full p-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={selectedModelId}
                  onChange={(e) => setSelectedModelId(e.target.value)}
                  disabled={loadingPrediction}
                >
                  <option value="">Selecione um modelo GRU</option>
                  {gruModels.map((model) => (
                    <option key={model.id} value={model.id}>
                      Modelo GRU - {new Date(model.created_at).toLocaleDateString('pt-BR')} 
                      {model.data_start_date && model.data_end_date && 
                        ` (Dados: ${new Date(model.data_start_date).toLocaleDateString('pt-BR')} - ${new Date(model.data_end_date).toLocaleDateString('pt-BR')})`
                      }
                    </option>
                  ))}
                </select>
                {gruModels.length === 0 && (
                  <p className="text-xs text-gray-500 mt-1">
                    Nenhum modelo GRU disponível para esta máquina
                  </p>
                )}
              </div>

              <button 
                onClick={handlePrediction}
                disabled={loadingPrediction || !selectedModelId || !selectedHorizon}
                className="w-full bg-green-600 text-white py-2 px-4 rounded text-sm font-medium hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loadingPrediction ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Gerando predição...
                  </>
                ) : (
                  'Realizar previsão'
                )}
              </button>
            </div>
          </div>

          {/* Machine Data */}
          <div className="border-t pt-6">
            <h3 className="font-bold text-gray-800 mb-4">Dados da motobomba:</h3>
            
            {/* Engine Data */}
            <div className="mb-6">
              <h4 className="font-medium text-gray-700 mb-3 text-sm">🔧 Dados do Motor:</h4>
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div className="space-y-2">
                  <div><span className="font-medium text-blue-600">RPM:</span> {formatValue(machine.telemetry.rpm)}</div>
                  <div><span className="font-medium text-blue-600">Bateria:</span> {formatValue(machine.telemetry.bat, 'V', 1)}</div>
                  <div><span className="font-medium text-blue-600">Chave:</span> {formatValue(machine.telemetry.chave, 'V', 1)}</div>
                </div>
                <div className="space-y-2">
                  <div><span className="font-medium text-blue-600">Combustível:</span> {formatValue(machine.telemetry.fuel_level, 'L')}</div>
                  <div><span className="font-medium text-blue-600">Consumo:</span> {formatValue(machine.telemetry.fuel_consumption, 'L/h', 1)}</div>
                  <div><span className="font-medium text-blue-600">Temperatura:</span> {formatValue(machine.telemetry.coolant_temp, '°C', 1)}</div>
                </div>
                <div className="space-y-2">
                  <div><span className="font-medium text-blue-600">Pressão Óleo:</span> {formatValue(machine.telemetry.oil_pressure, ' bar', 1)}</div>
                  <div><span className="font-medium text-blue-600">Nível Óleo:</span> {formatValue(machine.telemetry.oil_level, 'L')}</div>
                  <div><span className="font-medium text-blue-600">Horas Motor:</span> {formatValue(machine.telemetry.engine_runtime_hours, 'h')}</div>
                </div>
                <div className="space-y-2">
                  <div><span className="font-medium text-blue-600">Nº Partidas:</span> {formatValue(machine.telemetry.starts_number)}</div>
                  <div><span className="font-medium text-blue-600">Status:</span> <span className="capitalize font-medium">{machine.status}</span></div>
                  <div><span className="font-medium text-blue-600">Atualização:</span></div>
                  <div className="text-xs text-gray-500">{machine.lastUpdate}</div>
                </div>
              </div>
            </div>
            
            {/* Pump Data */}
            <div className="mb-6">
              <h4 className="font-medium text-gray-700 mb-3 text-sm">💧 Dados da Bomba:</h4>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div><span className="font-medium text-green-600">Recalque:</span> {formatValue(machine.telemetry.recalque, ' bar', 1)}</div>
                <div><span className="font-medium text-green-600">Sucção:</span> {formatValue(machine.telemetry.succao, ' bar', 1)}</div>
                <div><span className="font-medium text-green-600">Vibração:</span> {formatValue(machine.telemetry.vibration, ' Hz', 1)}</div>
              </div>
            </div>
            
            {/* LED Status */}
            <div className="mb-6">
              <h4 className="font-medium text-gray-700 mb-3 text-sm">💡 Status dos LEDs:</h4>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${machine.telemetry.led_auto === 1 ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                  <span className="font-medium text-green-600">Automático:</span> 
                  <span>{machine.telemetry.led_auto === 1 ? 'ATIVO' : machine.telemetry.led_auto === 0 ? 'INATIVO' : '--'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${machine.telemetry.led_manual === 1 ? 'bg-yellow-500' : 'bg-gray-300'}`}></div>
                  <span className="font-medium text-yellow-600">Manual:</span> 
                  <span>{machine.telemetry.led_manual === 1 ? 'ATIVO' : machine.telemetry.led_manual === 0 ? 'INATIVO' : '--'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${machine.telemetry.led_stop === 1 ? 'bg-red-500' : 'bg-gray-300'}`}></div>
                  <span className="font-medium text-red-600">Parada:</span> 
                  <span>{machine.telemetry.led_stop === 1 ? 'ATIVO' : machine.telemetry.led_stop === 0 ? 'INATIVO' : '--'}</span>
                </div>
              </div>
            </div>
            
            {/* Location Data */}
            {(machine.telemetry.latitude !== undefined && machine.telemetry.longitude !== undefined) && (
              <div className="mb-6">
                <h4 className="font-medium text-gray-700 mb-3 text-sm">📍 Localização:</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="font-medium text-purple-600">Latitude:</span> {formatValue(machine.telemetry.latitude, '°', 6)}</div>
                  <div><span className="font-medium text-purple-600">Longitude:</span> {formatValue(machine.telemetry.longitude, '°', 6)}</div>
                </div>
              </div>
            )}
            
            {/* Seção de Alarmes e Eventos */}
            {(machine.alarms && machine.alarms.length > 0) && (
              <div className="mt-4 p-3 bg-red-50 rounded-lg">
                <h4 className="font-medium text-red-800 mb-2">⚠️ Alarmes Recentes:</h4>
                <div className="space-y-1 text-sm">
                  {machine.alarms.slice(0, 3).map((alarm, index) => (
                    <div key={index} className="text-red-700">
                      {alarm.message}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {(machine.events && machine.events.length > 0) && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-800 mb-2">📋 Eventos Recentes:</h4>
                <div className="space-y-1 text-sm">
                  {machine.events.slice(0, 3).map((event, index) => (
                    <div key={index} className="text-blue-700">
                      {event.message}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};