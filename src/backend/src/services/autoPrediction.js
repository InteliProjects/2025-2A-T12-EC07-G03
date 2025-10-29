import { query } from './db.js';

class AutoPredictionService {
  constructor() {
    this.intervalId = null;
    this.isRunning = false;
    this.PREDICTION_INTERVAL = 60000; // 1 minuto em milissegundos
  }

  /**
   * Busca todas as máquinas disponíveis
   */
  async getMachines() {
    try {
      const sql = `
        SELECT DISTINCT motor_pump as name
        FROM processed_data
        WHERE motor_pump IS NOT NULL
        ORDER BY motor_pump ASC
      `;
      
      const result = await query(sql);
      return result.rows.map(row => row.name);
    } catch (error) {
      console.error('Erro ao buscar máquinas:', error);
      return [];
    }
  }

  /**
   * Busca o melhor modelo para uma máquina específica
   */
  async getBestModel(machineName) {
    try {
      const sql = `
        SELECT 
          id,
          machine_name,
          bucket_address,
          metrics
        FROM models
        WHERE machine_name = $1
        ORDER BY 
          (metrics->'classification_report'->'weighted avg'->>'f1-score')::float DESC,
          timestamp DESC
        LIMIT 1
      `;
      
      const result = await query(sql, [machineName]);
      
      if (result.rows.length === 0) {
        return null;
      }
      
      return result.rows[0];
    } catch (error) {
      console.error(`Erro ao buscar melhor modelo para ${machineName}:`, error);
      return null;
    }
  }

  /**
   * Faz predição para uma máquina específica
   */
  async predictForMachine(machineName, bucketAddress) {
    try {
      const response = await fetch('http://localhost:3000/machine/xgboost/predict', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json', 
          'accept': 'application/json' 
        },
        body: JSON.stringify({
          machine_name: machineName,
          model_bucket_address: bucketAddress
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const predictionResult = await response.json();
      
      // Salvar predição no banco
      await this.savePrediction(machineName, bucketAddress, predictionResult);
      
      return predictionResult;
    } catch (error) {
      console.error(`Erro ao fazer predição para ${machineName}:`, error.message);
      return null;
    }
  }

  /**
   * Salva a predição no banco de dados
   */
  async savePrediction(machineName, bucketAddress, predictionResult) {
    try {
      const sql = `
        INSERT INTO predictions (motor_pump, model_bucket_addres, prediction, timestamp)
        VALUES ($1, $2, $3, NOW())
      `;
      
      await query(sql, [
        machineName,
        bucketAddress || 'ainda_não_implementado',
        JSON.stringify(predictionResult)
      ]);
      
      console.log(`✓ Predição salva para ${machineName}`);
    } catch (error) {
      console.error(`Erro ao salvar predição para ${machineName}:`, error);
    }
  }

  /**
   * Executa predições para todas as máquinas
   */
  async runPredictions() {
    console.log(`[${new Date().toISOString()}] Iniciando ciclo de predições automáticas...`);
    
    try {
      const machines = await this.getMachines();
      console.log(`  → ${machines.length} máquinas encontradas`);
      
      if (machines.length === 0) {
        console.log('  → Nenhuma máquina disponível para predição');
        return;
      }

      const results = [];
      
      for (const machineName of machines) {
        try {
          // Buscar melhor modelo para esta máquina
          const bestModel = await this.getBestModel(machineName);
          
          if (!bestModel) {
            console.log(`  ⚠ Nenhum modelo encontrado para ${machineName}`);
            continue;
          }

          console.log(`  → Fazendo predição para ${machineName} (modelo: ${bestModel.bucket_address})`);
          
          // Fazer predição
          const prediction = await this.predictForMachine(
            machineName,
            bestModel.bucket_address
          );
          
          if (prediction) {
            results.push({
              machine: machineName,
              success: true,
              prediction: prediction.results?.[0]?.status || 'UNKNOWN'
            });
          } else {
            results.push({
              machine: machineName,
              success: false,
              error: 'Falha na predição'
            });
          }
          
        } catch (error) {
          console.error(`  ✗ Erro ao processar ${machineName}:`, error.message);
          results.push({
            machine: machineName,
            success: false,
            error: error.message
          });
        }
      }
      
      const successCount = results.filter(r => r.success).length;
      console.log(`[${new Date().toISOString()}] Ciclo concluído: ${successCount}/${machines.length} predições bem-sucedidas`);
      
    } catch (error) {
      console.error('Erro ao executar ciclo de predições:', error);
    }
  }

  /**
   * Inicia o serviço de predições automáticas
   */
  start() {
    if (this.isRunning) {
      console.log('⚠ Serviço de predições automáticas já está em execução');
      return;
    }

    console.log('🚀 Iniciando serviço de predições automáticas...');
    console.log(`   Intervalo: ${this.PREDICTION_INTERVAL / 1000} segundos`);
    
    this.isRunning = true;
    
    // Executar imediatamente na primeira vez
    this.runPredictions();
    
    // Configurar intervalo
    this.intervalId = setInterval(() => {
      this.runPredictions();
    }, this.PREDICTION_INTERVAL);
    
    console.log('✓ Serviço de predições automáticas iniciado com sucesso');
  }

  /**
   * Para o serviço de predições automáticas
   */
  stop() {
    if (!this.isRunning) {
      console.log('⚠ Serviço de predições automáticas não está em execução');
      return;
    }

    console.log('🛑 Parando serviço de predições automáticas...');
    
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    
    this.isRunning = false;
    console.log('✓ Serviço de predições automáticas parado');
  }

  /**
   * Retorna o status do serviço
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      interval: this.PREDICTION_INTERVAL,
      intervalSeconds: this.PREDICTION_INTERVAL / 1000
    };
  }
}

// Singleton instance
const autoPredictionService = new AutoPredictionService();

export default autoPredictionService;
