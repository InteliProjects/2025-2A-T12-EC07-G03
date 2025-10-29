import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { 
  PieChart, 
  Bot, 
  ChevronDown, 
  Search,
  User,
  LogOut,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import api from '@/lib/api';

const ModelsPage = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [selectedMachine, setSelectedMachine] = useState('');
  const [selectedIndicator, setSelectedIndicator] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isTraining, setIsTraining] = useState(false);
  const [trainingProcessId, setTrainingProcessId] = useState<string | null>(null);
  const [trainingStatus, setTrainingStatus] = useState<string | null>(null);
  const [availableMachines, setAvailableMachines] = useState<string[]>([]);
  const [loadingMachines, setLoadingMachines] = useState(true);
  const [trainingJobs, setTrainingJobs] = useState<any[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [models, setModels] = useState<any[]>([]);
  const [loadingModels, setLoadingModels] = useState(true);
  const [filteredModels, setFilteredModels] = useState<any[]>([]);
  const [filterMachine, setFilterMachine] = useState('all');
  const [filterIndicator, setFilterIndicator] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'accuracy' | 'precision' | 'recall' | 'f1'>('date');
  const [deletingModelId, setDeletingModelId] = useState<number | null>(null);
  const [modelToDelete, setModelToDelete] = useState<any | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  
  // Usar ref para manter a referência dos jobs sem causar re-render
  const trainingJobsRef = useRef<any[]>([]);

  const handleLogout = async () => {
    await logout();
  };

  // Buscar máquinas disponíveis ao carregar o componente
  useEffect(() => {
    const fetchMachines = async () => {
      try {
        setLoadingMachines(true);
        const response = await api.get('/api/data/machines');
        if (response.data.success) {
          setAvailableMachines(response.data.machines);
        }
      } catch (error) {
        console.error('Erro ao buscar máquinas:', error);
        toast({
          title: "Erro ao carregar máquinas",
          description: "Não foi possível carregar a lista de máquinas disponíveis",
          variant: "destructive"
        });
      } finally {
        setLoadingMachines(false);
      }
    };

    fetchMachines();
  }, [toast]);

  // Buscar modelos disponíveis
  useEffect(() => {
    const fetchModels = async () => {
      try {
        setLoadingModels(true);
        const response = await api.get('/api/models');
        if (response.data.success) {
          setModels(response.data.models);
        }
      } catch (error) {
        console.error('Erro ao buscar modelos:', error);
        toast({
          title: "Erro ao carregar modelos",
          description: "Não foi possível carregar os modelos disponíveis",
          variant: "destructive"
        });
      } finally {
        setLoadingModels(false);
      }
    };

    fetchModels();
  }, [toast]);

  // Filtrar e ordenar modelos
  useEffect(() => {
    let filtered = [...models];

    // Filtrar por máquina
    if (filterMachine !== 'all') {
      filtered = filtered.filter(m => m.machine_name === filterMachine);
    }

    // Filtrar por indicador
    if (filterIndicator !== 'all') {
      filtered = filtered.filter(m => m.indicator.toLowerCase() === filterIndicator);
    }

    // Filtrar por tipo de modelo
    if (filterType !== 'all') {
      filtered = filtered.filter(m => m.type.toLowerCase() === filterType.toLowerCase());
    }

    // Filtrar por termo de pesquisa
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(m => 
        m.machine_name.toLowerCase().includes(term) ||
        m.type.toLowerCase().includes(term) ||
        m.indicator.toLowerCase().includes(term)
      );
    }

    // Ordenar
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'accuracy':
          return parseFloat(b.metrics.accuracy) - parseFloat(a.metrics.accuracy);
        case 'precision':
          return parseFloat(b.metrics.precision) - parseFloat(a.metrics.precision);
        case 'recall':
          return parseFloat(b.metrics.recall) - parseFloat(a.metrics.recall);
        case 'f1':
          return parseFloat(b.metrics.f1_score) - parseFloat(a.metrics.f1_score);
        case 'date':
        default:
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    });

    setFilteredModels(filtered);
  }, [models, filterMachine, filterIndicator, filterType, searchTerm, sortBy]);

  // Buscar training jobs de forma otimizada
  const fetchTrainingJobs = useCallback(async (isInitial = false) => {
    try {
      // Apenas mostrar loading na primeira carga
      if (isInitial) {
        setLoadingJobs(true);
      }
      
      const response = await api.get('/api/training-jobs');
      if (response.data.success) {
        // Ordenar: 1) Em execução primeiro, 2) Por data (mais recente)
        const newJobs = response.data.jobs.sort((a: any, b: any) => {
          // Jobs "running" sempre no topo
          if (a.status === 'running' && b.status !== 'running') return -1;
          if (a.status !== 'running' && b.status === 'running') return 1;
          
          // Se ambos são "running" ou nenhum é, ordenar por data
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        });
        
        // Comparar apenas se os dados mudaram
        const currentJobsStr = JSON.stringify(trainingJobsRef.current);
        const newJobsStr = JSON.stringify(newJobs);
        
        if (currentJobsStr !== newJobsStr) {
          trainingJobsRef.current = newJobs;
          setTrainingJobs(newJobs);
        }
      }
    } catch (error) {
      console.error('Erro ao buscar training jobs:', error);
      // Só mostrar erro na primeira tentativa
      if (isInitial) {
        toast({
          title: "Erro ao carregar jobs",
          description: "Não foi possível carregar os jobs de treinamento",
          variant: "destructive"
        });
      }
    } finally {
      if (isInitial) {
        setLoadingJobs(false);
      }
    }
  }, [toast]);

  useEffect(() => {
    // Busca inicial
    fetchTrainingJobs(true);
    
    // Polling a cada 5 segundos sem recarregar o componente
    const interval = setInterval(() => fetchTrainingJobs(false), 5000);
    
    return () => clearInterval(interval);
  }, [fetchTrainingJobs]);

  // Monitorar status do treinamento
  useEffect(() => {
    if (trainingProcessId && trainingStatus !== 'finished' && trainingStatus !== 'failed') {
      const interval = setInterval(async () => {
        try {
          const response = await api.get(`/model-training/status/${trainingProcessId}`);
          setTrainingStatus(response.data.status);
          
          if (response.data.status === 'finished') {
            toast({
              title: "Treinamento concluído!",
              description: `Modelo treinado com sucesso para ${selectedMachine}`,
            });
            setIsTraining(false);
            clearInterval(interval);
          } else if (response.data.status === 'failed') {
            toast({
              title: "Erro no treinamento",
              description: response.data.error_message || "Falha ao treinar modelo",
              variant: "destructive"
            });
            setIsTraining(false);
            clearInterval(interval);
          }
        } catch (error) {
          console.error('Erro ao verificar status:', error);
        }
      }, 3000); // Verifica a cada 3 segundos

      return () => clearInterval(interval);
    }
  }, [trainingProcessId, trainingStatus, selectedMachine, toast]);

  // Iniciar treinamento
  const handleStartTraining = async () => {
    if (!selectedMachine || !selectedIndicator) {
      toast({
        title: "Campos obrigatórios",
        description: "Selecione a máquina e o indicador",
        variant: "destructive"
      });
      return;
    }

    setIsTraining(true);
    
    try {
      const payload: Record<string, string> = {
        machine_name: selectedMachine,
        indicator: selectedIndicator === 'funcionamento' ? 'status' : 'health'
      };

      if (startDate) payload.start_date = startDate;
      if (endDate) payload.end_date = endDate;

      const response = await api.post('/model-training/train', payload) as { process_id: string; status: string };
      
      setTrainingProcessId(response.process_id);
      setTrainingStatus(response.status);
      
      toast({
        title: "Treinamento iniciado!",
        description: "O treinamento estará pronto em breve.",
      });

      // Atualizar lista de jobs imediatamente usando a função otimizada
      fetchTrainingJobs(false);
    } catch (error) {
      const err = error as Error;
      toast({
        title: "Erro ao iniciar treinamento",
        description: err.message,
        variant: "destructive"
      });
      setIsTraining(false);
    }
  };

  // Fazer predição
  const handlePredict = async (machineId: string, indicator: string) => {
    try {
      const endpoint = indicator === 'Funcionamento' 
        ? '/model-inference/machine/xgboost/predict'
        : '/model-inference/machine/gru/predict';
      
      const payload = indicator === 'Funcionamento'
        ? { machine_name: machineId }
        : { machine_name: machineId, time_steps: 60 };

      const response = await api.post(endpoint, payload);
      
      toast({
        title: "Predição realizada!",
        description: `Resultado obtido com sucesso`,
      });
      
      // Aqui você pode abrir um modal com os resultados detalhados
      console.log('Resultado da predição:', response);
    } catch (error) {
      const err = error as Error;
      toast({
        title: "Erro na predição",
        description: err.message,
        variant: "destructive"
      });
    }
  };

  // Abrir modal de confirmação de exclusão
  const handleDeleteClick = (model: any) => {
    setModelToDelete(model);
    setShowDeleteDialog(true);
  };

  // Confirmar exclusão do modelo
  const confirmDeleteModel = async () => {
    if (!modelToDelete) return;

    try {
      setDeletingModelId(modelToDelete.id);
      const response = await api.delete(`/api/models/${modelToDelete.id}`);
      
      if (response.data.success) {
        toast({
          title: "Modelo excluído!",
          description: "O modelo foi removido com sucesso",
        });
        
        // Atualizar lista de modelos
        setModels(models.filter(m => m.id !== modelToDelete.id));
        setShowDeleteDialog(false);
        setModelToDelete(null);
      }
    } catch (error) {
      const err = error as Error;
      toast({
        title: "Erro ao excluir modelo",
        description: err.message,
        variant: "destructive"
      });
    } finally {
      setDeletingModelId(null);
    }
  };

  // Cancelar exclusão
  const cancelDelete = () => {
    setShowDeleteDialog(false);
    setModelToDelete(null);
  };

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

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
                src={user?.avatar}
                alt="User Avatar"
                className="w-10 h-10 rounded-full"
              />
              <span className="text-gray-700 font-medium">{user?.name}</span>
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
            <button 
              onClick={() => navigate('/dashboard')}
              className="w-full h-12 flex items-center px-2 py-3 text-gray-600 hover:bg-gray-50 rounded-lg relative"
            >
              <div className="w-full flex justify-center group-hover:justify-start group-hover:pl-2 transition-all duration-300">
                <PieChart className="w-4 h-4 min-w-[1rem]" />
              </div>
              <span className="absolute left-10 opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap">
                Dashboard
              </span>
            </button>
            <button className="w-full h-12 flex items-center px-2 py-3 bg-[#1934A5] text-white rounded-lg font-medium relative">
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
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">Modelos</h1>
            
            {/* Top Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Novo Modelo Card */}
              <div className="bg-[#1934A5] rounded-lg p-6 text-white">
                <h2 className="text-xl font-semibold mb-4">Novo Modelo</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Selecione a máquina</label>
                    <Select value={selectedMachine} onValueChange={setSelectedMachine} disabled={loadingMachines}>
                      <SelectTrigger className="w-full bg-white text-black">
                        <SelectValue placeholder={loadingMachines ? "Carregando máquinas..." : "Selecione a máquina"} />
                      </SelectTrigger>
                      <SelectContent>
                        {availableMachines.length > 0 ? (
                          availableMachines.map((machine) => (
                            <SelectItem key={machine} value={machine}>
                              {machine}
                            </SelectItem>
                          ))
                        ) : (
                          <SelectItem value="no-machines" disabled>
                            Nenhuma máquina disponível
                          </SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Selecione o indicador</label>
                    <Select value={selectedIndicator} onValueChange={setSelectedIndicator}>
                      <SelectTrigger className="w-full bg-white text-black">
                        <SelectValue placeholder="Selecione o indicador" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="funcionamento">Funcionamento</SelectItem>
                        <SelectItem value="saude">Saúde</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Data inicial</label>
                      <Input 
                        type="date" 
                        className="bg-white text-black" 
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">Data final</label>
                      <Input 
                        type="date" 
                        className="bg-white text-black" 
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                      />
                    </div>
                  </div>
                  <Button 
                    className="w-full bg-green-600 hover:bg-green-700 text-white mt-4"
                    onClick={handleStartTraining}
                    disabled={isTraining}
                  >
                    {isTraining ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Treinando... ({trainingStatus || 'iniciando'})
                      </>
                    ) : (
                      'Realizar treinamento'
                    )}
                  </Button>
                </div>
              </div>

              {/* Training Jobs Card */}
              <div className="bg-[#1934A5] rounded-lg p-6 text-white max-h-[376px] overflow-y-auto">
                <h2 className="text-xl font-semibold mb-4">Treinamentos em Andamento</h2>
                {loadingJobs ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="ml-2">Carregando...</span>
                  </div>
                ) : trainingJobs.length === 0 ? (
                  <div className="text-sm opacity-90">Nenhum treinamento encontrado</div>
                ) : (
                  <div className="space-y-3 text-sm">
                    {trainingJobs.map((job) => (
                      <div 
                        key={job.id} 
                        className="bg-white/10 rounded-lg p-3 border border-white/20"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-semibold">{job.machine_name}</span>
                          <span className={`px-2 py-1 rounded text-xs font-medium flex items-center gap-1 ${
                            job.status === 'pending' ? 'bg-yellow-500/20 border border-yellow-500/50' :
                            job.status === 'running' ? 'bg-blue-500/20 border border-blue-500/50' :
                            job.status === 'finished' ? 'bg-green-500/20 border border-green-500/50' :
                            job.status === 'failed' ? 'bg-red-500/20 border border-red-500/50' :
                            'bg-gray-500/20 border border-gray-500/50'
                          }`}>
                            {job.status === 'finished' && <CheckCircle2 className="w-3 h-3" />}
                            {job.status === 'running' && <Loader2 className="w-3 h-3 animate-spin" />}
                            {job.status === 'failed' && <XCircle className="w-3 h-3" />}
                            {job.status === 'pending' && <Clock className="w-3 h-3" />}
                            {job.status === 'pending' && 'Pendente'}
                            {job.status === 'running' && 'Em Treinamento'}
                            {job.status === 'finished' && 'Concluído'}
                            {job.status === 'failed' && 'Falhou'}
                            {!['pending', 'running', 'finished', 'failed'].includes(job.status) && job.status}
                          </span>
                        </div>
                        <div className="space-y-1 text-xs opacity-90">
                          <div>Indicador: {job.indicator === 'status' ? 'Funcionamento' : 'Saúde'}</div>
                          {job.start_date && job.end_date && (
                            <div>
                              Dados: {new Date(job.start_date).toLocaleDateString('pt-BR')} a {new Date(job.end_date).toLocaleDateString('pt-BR')}
                            </div>
                          )}
                          <div>Iniciado: {new Date(job.created_at).toLocaleString('pt-BR')}</div>
                          {job.finished_at && (
                            <div>Finalizado: {new Date(job.finished_at).toLocaleString('pt-BR')}</div>
                          )}
                          {job.error_message && (
                            <div className="text-red-300 mt-2">Erro: {job.error_message}</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Available Models Section */}
            <div className="bg-white rounded-lg shadow-sm">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Modelos Disponíveis</h2>
                
                {/* Filters */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
                  <Select value={filterMachine} onValueChange={setFilterMachine}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Máquina" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todas</SelectItem>
                      {availableMachines.map((machine) => (
                        <SelectItem key={machine} value={machine}>
                          {machine}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  <Select value={filterIndicator} onValueChange={setFilterIndicator}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Indicador" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos</SelectItem>
                      <SelectItem value="funcionamento">Funcionamento</SelectItem>
                      <SelectItem value="saude">Saúde</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <Select value={filterType} onValueChange={setFilterType}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Tipo de Modelo" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos</SelectItem>
                      <SelectItem value="xgboost">XGBoost</SelectItem>
                      <SelectItem value="gru">GRU</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Ordenar por" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="date">Data (mais recente)</SelectItem>
                      <SelectItem value="accuracy">Acurácia (%)</SelectItem>
                      <SelectItem value="precision">Precisão (%)</SelectItem>
                      <SelectItem value="recall">Recall (%)</SelectItem>
                      <SelectItem value="f1">F1-Score (%)</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input 
                      placeholder="Pesquisar" 
                      className="pl-10"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                </div>
              </div>
              
              {/* Models List */}
              <div className="p-6 space-y-4">
                {loadingModels ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-6 h-6 animate-spin text-[#1934A5]" />
                    <span className="ml-2 text-gray-600">Carregando modelos...</span>
                  </div>
                ) : filteredModels.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    {models.length === 0 ? 'Nenhum modelo disponível' : 'Nenhum modelo encontrado com os filtros selecionados'}
                  </div>
                ) : (
                  filteredModels.map((model) => (
                    <div key={model.id} className="border border-gray-200 rounded-lg p-4 hover:border-[#1934A5] transition-colors">
                      <div className="flex justify-between items-start mb-3">
                        <h3 className="font-semibold text-gray-900">
                          Modelo {model.type} - {model.indicator}
                        </h3>
                        <span className="text-xs text-gray-500">
                          {new Date(model.created_at).toLocaleDateString('pt-BR')}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 text-sm text-gray-600 mb-4">
                        <div>
                          <span className="font-medium">Máquina:</span> {model.machine_name}
                        </div>
                        <div>
                          <span className="font-medium">Tipo:</span> {model.type}
                        </div>
                        <div>
                          <span className="font-medium">Indicador:</span> {model.indicator}
                        </div>
                        <div>
                          <span className="font-medium">Período:</span><br />
                          {new Date(model.data_start_date).toLocaleDateString('pt-BR')} a {new Date(model.data_end_date).toLocaleDateString('pt-BR')}
                        </div>
                      </div>
                      
                      {/* Metrics */}
                      <div className="bg-gray-50 rounded-lg p-4 mb-4">
                        <h4 className="font-semibold text-gray-700 mb-3">Métricas do Modelo</h4>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                          <div className="text-center">
                            <div className="text-2xl font-bold text-[#1934A5]">{model.metrics.accuracy}%</div>
                            <div className="text-xs text-gray-500 mt-1">Acurácia</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-green-600">{model.metrics.precision}%</div>
                            <div className="text-xs text-gray-500 mt-1">Precisão</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-blue-600">{model.metrics.recall}%</div>
                            <div className="text-xs text-gray-500 mt-1">Recall</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-purple-600">{model.metrics.f1_score}%</div>
                            <div className="text-xs text-gray-500 mt-1">F1-Score</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-orange-600">{model.metrics.auc_score}%</div>
                            <div className="text-xs text-gray-500 mt-1">AUC Score</div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          className="text-[#1934A5] border-[#1934A5] hover:bg-[#1934A5] hover:text-white"
                          onClick={() => handlePredict(model.machine_name, model.indicator)}
                        >
                          Fazer Predição
                        </Button>
                        <Button 
                          variant="outline"
                          className="text-red-600 border-red-600 hover:bg-red-600 hover:text-white"
                          onClick={() => handleDeleteClick(model)}
                          disabled={deletingModelId === model.id}
                        >
                          {deletingModelId === model.id ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Excluindo...
                            </>
                          ) : (
                            'Excluir modelo'
                          )}
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Modal de Confirmação de Exclusão */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <DialogTitle className="text-xl">Excluir Modelo</DialogTitle>
            </div>
            <DialogDescription className="text-base pt-2">
              Tem certeza que deseja excluir este modelo? Esta ação não pode ser desfeita.
            </DialogDescription>
          </DialogHeader>
          
          {modelToDelete && (
            <div className="bg-gray-50 rounded-lg p-4 my-4">
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Modelo:</span>{' '}
                  <span className="text-gray-900">{modelToDelete.type} - {modelToDelete.indicator}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Máquina:</span>{' '}
                  <span className="text-gray-900">{modelToDelete.machine_name}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Criado em:</span>{' '}
                  <span className="text-gray-900">
                    {new Date(modelToDelete.created_at).toLocaleDateString('pt-BR')}
                  </span>
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={cancelDelete}
              disabled={deletingModelId !== null}
            >
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDeleteModel}
              disabled={deletingModelId !== null}
            >
              {deletingModelId !== null ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Excluindo...
                </>
              ) : (
                'Sim, excluir modelo'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ModelsPage;