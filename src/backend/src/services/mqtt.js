import mqtt from 'mqtt';
import { env } from '../utils/env.js';
import { EventEmitter } from 'events';

// Classe para processamento e limpeza de dados MQTT (baseado no pipeline de data cleaning)
class DataCleaner {
  constructor() {
    // Valores sentinela que indicam "sem dado" ou "erro de leitura"
    this.invalidSentinels = [2147483643, 2147483644, 2147483645, 2147483646, 2147483647, -1];
    this.maxValidValue = 20000; // Valores acima disso são considerados inválidos
  }

  /**
   * Verifica se um valor é válido (não é sentinela e não é muito alto)
   */
  isValidValue(value) {
    if (value === null || value === undefined) return false;
    if (this.invalidSentinels.includes(value)) return false;
    if (Math.abs(value) > this.maxValidValue) return false;
    return true;
  }

  /**
   * Limpa e processa um valor baseado no tipo de recurso
   */
  cleanValue(value, resourceType) {
    // Se valor é inválido, retorna null
    if (!this.isValidValue(value)) {
      return null;
    }

    // Bateria e alternador precisam ser divididos por 10
    if (resourceType === 'Bat_V' || resourceType === 'Char_V') {
      return value / 10;
    }

    // Para outros valores, retorna como está
    return value;
  }

  /**
   * Extrai o tipo de recurso do tópico MQTT
   */
  extractResourceType(topic) {
    const parts = topic.split('/');
    return parts[parts.length - 1]; // Último elemento do tópico
  }

  /**
   * Processa dados JSON do payload MQTT
   */
  processPayload(payload, topic) {
    try {
      const jsonData = JSON.parse(payload);
      const resourceType = this.extractResourceType(topic);
      
      // Extrair valor do JSON baseado na estrutura observada
      const deviceKeys = Object.keys(jsonData);
      if (deviceKeys.length > 0) {
        const deviceData = jsonData[deviceKeys[0]];
        const portKeys = Object.keys(deviceData);
        if (portKeys.length > 0) {
          const portData = deviceData[portKeys[0]];
          const registerKeys = Object.keys(portData);
          if (registerKeys.length > 0) {
            const rawValue = portData[registerKeys[0]];
            const cleanedValue = this.cleanValue(rawValue, resourceType);
            
            return {
              value: cleanedValue,
              isValid: cleanedValue !== null,
              resourceType: resourceType,
              rawValue: rawValue
            };
          }
        }
      }
    } catch (error) {
      // Se não for JSON, tentar como número direto
      const resourceType = this.extractResourceType(topic);
      const directValue = parseFloat(payload);
      if (!isNaN(directValue)) {
        const cleanedValue = this.cleanValue(directValue, resourceType);
        return {
          value: cleanedValue,
          isValid: cleanedValue !== null,
          resourceType: resourceType,
          rawValue: directValue
        };
      }
    }
    
    return { value: null, isValid: false, resourceType: null };
  }
}

// Definição dos tópicos MQTT e IDs das máquinas
const MACHINE_IDS = [
  'ITU-317',
  'ITU-692', 
  'ITU-693',
  'ITU-701',
  'ITU-920',
  'ITU-415'
];

const MQTT_TOPICS = [
  // ITU-317
  'ITB/ITU-317/1912BDA4A090ABD/Latitude_Long',
  'ITB/ITU-317/1922CF24BCC/Eng/Bat_V',
  'ITB/ITU-317/1922CF24BCC/Eng/Char_V',
  'ITB/ITU-317/1922CF24BCC/Eng/Cool_T',
  'ITB/ITU-317/1922CF24BCC/Eng/EngRT_H',
  'ITB/ITU-317/1922CF24BCC/Eng/Eng_RPM',
  'ITB/ITU-317/1922CF24BCC/Eng/Fuel_Con',
  'ITB/ITU-317/1922CF24BCC/Eng/Fuel_L',
  'ITB/ITU-317/1922CF24BCC/Eng/Oil_L',
  'ITB/ITU-317/1922CF24BCC/Eng/Oil_P',
  'ITB/ITU-317/1922CF24BCC/Eng/Starts_N',
  'ITB/ITU-317/1922CF24BCC/Event',
  'ITB/ITU-317/1922CF24BCC/LED/Auto',
  'ITB/ITU-317/1922CF24BCC/LED/Man',
  'ITB/ITU-317/1922CF24BCC/LED/Stop',
  'ITB/ITU-317/1922CF24BCC/Pump/Recalque',
  'ITB/ITU-317/1922CF24BCC/Pump/Succao',
  'ITB/ITU-317/1922CF24BCC/Pump/Vibracao',
  
  // ITU-692
  'ITB/ITU-692/1912B09BE5484CD/Latitude_Long',
  'ITB/ITU-692/1922C49F1A9/Alarms',
  'ITB/ITU-692/1922C49F1A9/Eng/Bat_V',
  'ITB/ITU-692/1922C49F1A9/Eng/Char_V',
  'ITB/ITU-692/1922C49F1A9/Eng/Cool_T',
  'ITB/ITU-692/1922C49F1A9/Eng/EngRT_H',
  'ITB/ITU-692/1922C49F1A9/Eng/Eng_RPM',
  'ITB/ITU-692/1922C49F1A9/Eng/Fuel_Con',
  'ITB/ITU-692/1922C49F1A9/Eng/Fuel_L',
  'ITB/ITU-692/1922C49F1A9/Eng/Oil_L',
  'ITB/ITU-692/1922C49F1A9/Eng/Oil_P',
  'ITB/ITU-692/1922C49F1A9/Eng/Starts_N',
  'ITB/ITU-692/1922C49F1A9/Event',
  'ITB/ITU-692/1922C49F1A9/LED/Auto',
  'ITB/ITU-692/1922C49F1A9/LED/Man',
  'ITB/ITU-692/1922C49F1A9/LED/Stop',
  'ITB/ITU-692/1922C49F1A9/Pump/Recalque',
  'ITB/ITU-692/1922C49F1A9/Pump/Succao',
  'ITB/ITU-692/1922C49F1A9/Pump/Vibracao',
  
  // ITU-701
  'ITB/ITU-701/1912D4277CDEB10/Latitude_Long',
  'ITB/ITU-701/1922CEF375A/Alarms',
  'ITB/ITU-701/1922CEF375A/Eng/Bat_V',
  'ITB/ITU-701/1922CEF375A/Eng/Char_V',
  'ITB/ITU-701/1922CEF375A/Eng/Cool_T',
  'ITB/ITU-701/1922CEF375A/Eng/EngRT_H',
  'ITB/ITU-701/1922CEF375A/Eng/Eng_RPM',
  'ITB/ITU-701/1922CEF375A/Eng/Fuel_Con',
  'ITB/ITU-701/1922CEF375A/Eng/Fuel_L',
  'ITB/ITU-701/1922CEF375A/Eng/Oil_L',
  'ITB/ITU-701/1922CEF375A/Eng/Oil_P',
  'ITB/ITU-701/1922CEF375A/Eng/Starts_N',
  'ITB/ITU-701/1922CEF375A/Event',
  'ITB/ITU-701/1922CEF375A/LED/Auto',
  'ITB/ITU-701/1922CEF375A/LED/Man',
  'ITB/ITU-701/1922CEF375A/LED/Stop',
  'ITB/ITU-701/1922CEF375A/Pump/Recalque',
  'ITB/ITU-701/1922CEF375A/Pump/Succao',
  'ITB/ITU-701/1922CEF375A/Pump/Vibracao',
  
  // ITU-920
  'ITB/ITU-920/1912ED27844AA5C/Latitude_Long',
  'ITB/ITU-920/1922E6AEB13/Alarms',
  'ITB/ITU-920/1922E6AEB13/Eng/Bat_V',
  'ITB/ITU-920/1922E6AEB13/Eng/Char_V',
  'ITB/ITU-920/1922E6AEB13/Eng/Cool_T',
  'ITB/ITU-920/1922E6AEB13/Eng/EngRT_H',
  'ITB/ITU-920/1922E6AEB13/Eng/Eng_RPM',
  'ITB/ITU-920/1922E6AEB13/Eng/Fuel_Con',
  'ITB/ITU-920/1922E6AEB13/Eng/Fuel_L',
  'ITB/ITU-920/1922E6AEB13/Eng/Oil_L',
  'ITB/ITU-920/1922E6AEB13/Eng/Oil_P',
  'ITB/ITU-920/1922E6AEB13/Eng/Starts_N',
  'ITB/ITU-920/1922E6AEB13/Event',
  'ITB/ITU-920/1922E6AEB13/LED/Auto',
  'ITB/ITU-920/1922E6AEB13/LED/Man',
  'ITB/ITU-920/1922E6AEB13/LED/Stop',
  'ITB/ITU-920/1922E6AEB13/Pump/Recalque',
  'ITB/ITU-920/1922E6AEB13/Pump/Succao',
  'ITB/ITU-920/1922E6AEB13/Pump/Vibracao',
  
  // ITU-693
  'ITB/ITU-693/1912B09BE5484CD/Latitude_Long',
  'ITB/ITU-693/1922C49F1A9/Alarms',
  'ITB/ITU-693/1922C49F1A9/Eng/Bat_V',
  'ITB/ITU-693/1922C49F1A9/Eng/Char_V',
  'ITB/ITU-693/1922C49F1A9/Eng/Cool_T',
  'ITB/ITU-693/1922C49F1A9/Eng/EngRT_H',
  'ITB/ITU-693/1922C49F1A9/Eng/Eng_RPM',
  'ITB/ITU-693/1922C49F1A9/Eng/Fuel_Con',
  'ITB/ITU-693/1922C49F1A9/Eng/Fuel_L',
  'ITB/ITU-693/1922C49F1A9/Eng/Oil_L',
  'ITB/ITU-693/1922C49F1A9/Eng/Oil_P',
  'ITB/ITU-693/1922C49F1A9/Eng/Starts_N',
  'ITB/ITU-693/1922C49F1A9/Event',
  'ITB/ITU-693/1922C49F1A9/LED/Auto',
  'ITB/ITU-693/1922C49F1A9/LED/Man',
  'ITB/ITU-693/1922C49F1A9/LED/Stop',
  'ITB/ITU-693/1922C49F1A9/Pump/Recalque',
  'ITB/ITU-693/1922C49F1A9/Pump/Succao',
  'ITB/ITU-693/1922C49F1A9/Pump/Vibracao',
  
  // ITU-415
  'ITB/ITU-415/1912ED27844AA5C/Latitude_Long',
  'ITB/ITU-415/1922E6AEB13/Alarms',
  'ITB/ITU-415/1922E6AEB13/Eng/Bat_V',
  'ITB/ITU-415/1922E6AEB13/Eng/Char_V',
  'ITB/ITU-415/1922E6AEB13/Eng/Cool_T',
  'ITB/ITU-415/1922E6AEB13/Eng/EngRT_H',
  'ITB/ITU-415/1922E6AEB13/Eng/Eng_RPM',
  'ITB/ITU-415/1922E6AEB13/Eng/Fuel_Con',
  'ITB/ITU-415/1922E6AEB13/Eng/Fuel_L',
  'ITB/ITU-415/1922E6AEB13/Eng/Oil_L',
  'ITB/ITU-415/1922E6AEB13/Eng/Oil_P',
  'ITB/ITU-415/1922E6AEB13/Eng/Starts_N',
  'ITB/ITU-415/1922E6AEB13/Event',
  'ITB/ITU-415/1922E6AEB13/LED/Auto',
  'ITB/ITU-415/1922E6AEB13/LED/Man',
  'ITB/ITU-415/1922E6AEB13/LED/Stop',
  'ITB/ITU-415/1922E6AEB13/Pump/Recalque',
  'ITB/ITU-415/1922E6AEB13/Pump/Succao',
  'ITB/ITU-415/1922E6AEB13/Pump/Vibracao'
];

class MQTTService extends EventEmitter {
  constructor() {
    super();
    this.client = null;
    this._isConnected = false;
    this.machineData = new Map();
    this.lastUpdateTime = new Map();
    this.io = null; // Socket.IO instance
    this.connectionAttempts = 0;
    this.maxConnectionAttempts = 5;
    
    // Inicializar o limpador de dados
    this.dataCleaner = new DataCleaner();
    
    // Inicializar máquinas conhecidas estaticamente
    this.initializeMachines();
  }

  initializeMachines() {
    // Inicializar todas as máquinas conhecidas
    MACHINE_IDS.forEach(machineId => {
      this.machineData.set(machineId, {
        id: machineId,
        name: machineId,
        status: 'desconectado', // Começam desconectadas até receberem dados
        telemetry: {
          // Engine data
          rpm: undefined,
          bat: undefined,
          chave: undefined,
          fuel_level: undefined,
          fuel_consumption: undefined,
          oil_pressure: undefined,
          oil_level: undefined,
          coolant_temp: undefined,
          engine_runtime_hours: undefined,
          starts_number: undefined,
          
          // Pump data
          recalque: undefined,
          succao: undefined,
          vibration: undefined,
          
          // LED status
          led_auto: undefined,
          led_manual: undefined,
          led_stop: undefined,
          
          // Location
          latitude: undefined,
          longitude: undefined,
          
          // Deprecated/compatibility
          out: undefined
        },
        lastUpdate: new Date(),
        location: this.getMachineLocation(machineId),
        alarms: [],
        events: []
      });
      // Inicializar com timestamp antigo para marcar como desconectado
      this.lastUpdateTime.set(machineId, new Date(0));
    });
    
    console.log(`✓ ${MACHINE_IDS.length} máquinas inicializadas:`, MACHINE_IDS.join(', '));
  }

  getMachineLocation(machineId) {
    // Retornar localização baseada no ID da máquina
    const locations = {
      'ITU-317': 'Estação de Bombeamento Central',
      'ITU-692': 'Reservatório Norte',
      'ITU-693': 'Estação Principal',
      'ITU-701': 'Reservatório Sul',
      'ITU-920': 'Estação de Tratamento',
      'ITU-415': 'Estação de Distribuição'
    };
    return locations[machineId] || 'Principais dados de telemetria';
  }

  get isConnected() {
    return this._isConnected;
  }

  set isConnected(value) {
    this._isConnected = value;
  }

  setSocketIO(io) {
    this.io = io;
    
    // Emitir dados iniciais quando uma nova conexão WebSocket é estabelecida
    this.emitInitialData();
  }

  emitInitialData() {
    if (this.io) {
      // Emite dados iniciais de todas as máquinas
      const machines = this.getAllMachinesData();
      const summary = this.getDashboardSummary();
      const mqttStatus = { connected: this.isConnected };
      
      this.io.emit('initialData', {
        machines,
        summary,
        mqttStatus
      });
    }
  }

  connect() {
    try {
      this.connectionAttempts++;
      const protocol = env.MQTT_TLS ? 'mqtts' : 'mqtt';
      const brokerUrl = `${protocol}://${env.HOST_IP}:${env.HOST_PORT}`;
      
      // Iniciar emissão periódica de dados atuais
      this.startDataSimulation();
      
      const options = {
        clientId: `backend_${Math.random().toString(16).substr(2, 8)}`,
        clean: true,
        connectTimeout: parseInt(env.DISCOVERY_TIMEOUT) * 1000 || 4000,
        reconnectPeriod: 10000,
        keepalive: 60,
      };

      // Configurar autenticação se fornecida
      if (env.MQTT_USERNAME && env.MQTT_PASSWORD) {
        options.username = env.MQTT_USERNAME;
        options.password = env.MQTT_PASSWORD;
      }

      // Configurar TLS se necessário
      if (env.MQTT_TLS) {
        options.rejectUnauthorized = false;
      }

      this.client = mqtt.connect(brokerUrl, options);

      this.client.on('connect', () => {
        this.isConnected = true;
        this.connectionAttempts = 0;

        // Inscrever em TODOS os tópicos usando wildcard para descobrir quais máquinas estão ativas
        const wildcardTopic = 'ITB/#';
        
        this.client.subscribe(wildcardTopic, (err) => {
          if (err) {
            console.error('MQTT: Erro ao se inscrever nos tópicos:', err);
          }
        });

        // Emit WebSocket update
        if (this.io) {
          this.io.emit('mqttStatus', { connected: true });
        }

        this.emit('connected');
      });

      this.client.on('message', (topic, message) => {
        this.handleMessage(topic, message);
      });

      this.client.on('error', (error) => {
        console.error('❌ MQTT: Erro de conexão:', error.message);
        this.isConnected = false;
        
        // Emit WebSocket update
        if (this.io) {
          this.io.emit('mqttStatus', { connected: false, error: error.message });
        }
        
        // Retry connection if under max attempts
        if (this.connectionAttempts < this.maxConnectionAttempts) {
          setTimeout(() => this.connect(), 5000);
        }
      });

      this.client.on('close', () => {
        this.isConnected = false;
        
        // Emit WebSocket update
        if (this.io) {
          this.io.emit('mqttStatus', { connected: false });
        }
        
        this.emit('disconnected');
      });

    } catch (error) {
      console.error('Erro ao conectar ao broker MQTT:', error);
      this.isConnected = false;
    }
  }

  handleMessage(topic, message) {
    try {
      const payload = message.toString();
      const timestamp = new Date();
      
      // Extrair ID da máquina do tópico
      const machineId = this.extractMachineId(topic);
      if (!machineId) {
        return;
      }
      
      // Se a máquina não existe, criar dinamicamente
      if (!this.machineData.has(machineId)) {
        this.machineData.set(machineId, {
          id: machineId,
          name: machineId,
          status: 'desconhecido',
          telemetry: {
            // Engine data
            rpm: undefined,
            bat: undefined,
            chave: undefined,
            fuel_level: undefined,
            fuel_consumption: undefined,
            oil_pressure: undefined,
            oil_level: undefined,
            coolant_temp: undefined,
            engine_runtime_hours: undefined,
            starts_number: undefined,
            
            // Pump data
            recalque: undefined,
            succao: undefined,
            vibration: undefined,
            
            // LED status
            led_auto: undefined,
            led_manual: undefined,
            led_stop: undefined,
            
            // Location
            latitude: undefined,
            longitude: undefined,
            
            // Deprecated/compatibility
            out: undefined
          },
          lastUpdate: new Date(),
          location: 'Principais dados de telemetria',
          alarms: [],
          events: []
        });
        this.lastUpdateTime.set(machineId, new Date());
        
        // Emitir notificação de nova máquina descoberta
        if (this.io) {
          this.io.emit('newMachineDiscovered', { machineId });
        }
      }

      const machineData = this.machineData.get(machineId);
      
      // Usar o DataCleaner para processar e limpar os dados
      const cleanedData = this.dataCleaner.processPayload(payload, topic);
      
      if (!cleanedData.isValid) {
        return;
      }
      
      const value = cleanedData.value;
      const resourceType = cleanedData.resourceType;

      // Atualizar dados baseado no tipo de tópico
      let hasValidData = false;
      
      // Engine data
      if (topic.includes('/Eng/Eng_RPM')) {
        machineData.telemetry.rpm = value;
        hasValidData = true;
      } else if (topic.includes('/Eng/Bat_V')) {
        machineData.telemetry.bat = value; // DataCleaner já divide por 10
        hasValidData = true;
      } else if (topic.includes('/Eng/Char_V')) {
        machineData.telemetry.chave = value; // DataCleaner já divide por 10
        hasValidData = true;
      } else if (topic.includes('/Eng/Fuel_L')) {
        machineData.telemetry.fuel_level = value;
        hasValidData = true;
      } else if (topic.includes('/Eng/Fuel_Con')) {
        machineData.telemetry.fuel_consumption = value;
        hasValidData = true;
      } else if (topic.includes('/Eng/Oil_P')) {
        machineData.telemetry.oil_pressure = value;
        hasValidData = true;
      } else if (topic.includes('/Eng/Oil_L')) {
        machineData.telemetry.oil_level = value;
        hasValidData = true;
      } else if (topic.includes('/Eng/Cool_T')) {
        machineData.telemetry.coolant_temp = value;
        hasValidData = true;
      } else if (topic.includes('/Eng/EngRT_H')) {
        machineData.telemetry.engine_runtime_hours = value;
        hasValidData = true;
      } else if (topic.includes('/Eng/Starts_N')) {
        machineData.telemetry.starts_number = value;
        hasValidData = true;
      
      // Pump data
      } else if (topic.includes('/Pump/Vibracao')) {
        machineData.telemetry.vibration = value;
        hasValidData = true;
      } else if (topic.includes('/Pump/Recalque')) {
        machineData.telemetry.recalque = value;
        hasValidData = true;
      } else if (topic.includes('/Pump/Succao')) {
        machineData.telemetry.succao = value;
        hasValidData = true;
      
      // LED status
      } else if (topic.includes('/LED/Auto')) {
        machineData.telemetry.led_auto = value;
        hasValidData = true;
      } else if (topic.includes('/LED/Man')) {
        machineData.telemetry.led_manual = value;
        hasValidData = true;
      } else if (topic.includes('/LED/Stop')) {
        machineData.telemetry.led_stop = value;
        hasValidData = true;
      
      // Location data  
      } else if (topic.includes('/Latitude_Long')) {
        try {
          const locationData = JSON.parse(payload);
          if (locationData.lat !== undefined) {
            machineData.telemetry.latitude = locationData.lat;
          }
          if (locationData.lon !== undefined) {
            machineData.telemetry.longitude = locationData.lon;
          }
          hasValidData = true;
        } catch (e) {
          // Se não conseguir parsear coordenadas, continuar
        }
      } else if (topic.includes('/Alarms')) {
        if (payload && payload !== '0') {
          machineData.alarms.push({
            message: payload,
            timestamp: timestamp
          });
          if (machineData.alarms.length > 10) {
            machineData.alarms = machineData.alarms.slice(-10);
          }
        }
      } else if (topic.includes('/Event')) {
        if (payload) {
          machineData.events.push({
            message: payload,
            timestamp: timestamp
          });
          if (machineData.events.length > 10) {
            machineData.events = machineData.events.slice(-10);
          }
        }
      }

      if (hasValidData) {
        // Determinar status da máquina baseado nos dados
        machineData.status = this.determineStatus(machineData);
        machineData.lastUpdate = timestamp;
        this.lastUpdateTime.set(machineId, timestamp);
        
        // Emitir evento de atualização
        this.emit('machineUpdate', machineId, machineData);
        
        // Emit real-time update via WebSocket
        if (this.io) {
          this.io.emit('machineUpdate', {
            machineId,
            data: {
              ...machineData,
              lastUpdate: this.formatLastUpdate(machineData.lastUpdate)
            }
          });
          
          // Also emit updated summary
          this.io.emit('summaryUpdate', this.getDashboardSummary());
        }
      }

    } catch (error) {
      console.error('Erro ao processar mensagem MQTT:', error);
    }
  }

  extractMachineId(topic) {
    const match = topic.match(/ITB\/(ITU-\d+)\//);
    return match ? match[1] : null;
  }

  determineStatus(machineData) {
    const now = new Date();
    const lastUpdate = this.lastUpdateTime.get(machineData.id);
    const timeDiff = now - lastUpdate;

    // Se não recebeu dados nos últimos 30 segundos, considerar desconectado
    if (timeDiff > 30 * 1000) {
      return 'desconectado';
    }

    // Se tem alarmes recentes, considerar em manutenção
    if (machineData.alarms.length > 0) {
      const recentAlarms = machineData.alarms.filter(alarm => 
        (now - alarm.timestamp) < 10 * 60 * 1000
      );
      if (recentAlarms.length > 0) {
        return 'manutencao';
      }
    }

    // Se RPM > 0, está operando
    if (machineData.telemetry.rpm > 0) {
      return 'operando';
    }

    // Caso contrário, está parada
    return 'parada';
  }

  getAllMachinesData() {
    return Array.from(this.machineData.values()).map(machine => ({
      ...machine,
      lastUpdate: this.formatLastUpdate(machine.lastUpdate)
    }));
  }

  getMachineData(machineId) {
    const machine = this.machineData.get(machineId);
    if (!machine) return null;
    
    return {
      ...machine,
      lastUpdate: this.formatLastUpdate(machine.lastUpdate)
    };
  }

  formatLastUpdate(timestamp) {
    const now = new Date();
    const diff = now - timestamp;
    
    if (diff < 5000) { // menos de 5 segundos
      return 'agora mesmo';
    } else if (diff < 60000) { // menos de 1 minuto
      const seconds = Math.floor(diff / 1000);
      return `${seconds}s atrás`;
    } else if (diff < 3600000) { // menos de 1 hora
      const minutes = Math.floor(diff / 60000);
      return `${minutes}min atrás`;
    } else {
      const hours = Math.floor(diff / 3600000);
      return `${hours}h atrás`;
    }
  }

  getDashboardSummary() {
    const machines = this.getAllMachinesData();
    
    return {
      totalOperating: machines.filter(m => m.status === 'operando').length,
      machinesDown: machines.filter(m => m.status === 'parada' || m.status === 'desconectado').length,
      activeAlerts: machines.reduce((acc, m) => acc + (m.alarms?.length || 0), 0),
      upcomingMaintenance: machines.filter(m => m.status === 'manutencao').length
    };
  }

  startDataSimulation() {
    // Emitir os dados atuais periodicamente para garantir que o frontend receba atualizações
    setInterval(() => {
      if (this.io) {
        // Emite dados atuais de todas as máquinas
        this.machineData.forEach((machine, machineId) => {
          // Atualiza o status baseado no tempo desde a última atualização
          machine.status = this.determineStatus(machine);
          
          this.io.emit('machineUpdate', {
            machineId,
            data: {
              ...machine,
              lastUpdate: this.formatLastUpdate(machine.lastUpdate)
            }
          });
        });
        
        // Emite resumo atualizado
        this.io.emit('summaryUpdate', this.getDashboardSummary());
      }
    }, 2000); // A cada 2 segundos
  }

  disconnect() {
    if (this.client) {
      this.client.end();
      this.isConnected = false;
    }
  }
}

// Instância singleton
let mqttService = null;

export const getMQTTService = () => {
  if (!mqttService) {
    mqttService = new MQTTService();
  }
  return mqttService;
};

export default MQTTService;