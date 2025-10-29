import { Router } from 'express';
import { query } from '../services/db.js';
import { requireAuth } from '../middleware/auth.js';

const router = Router();

// Rota para buscar máquinas disponíveis
router.get('/machines', requireAuth, async (req, res) => {
  try {
    const sql = `
      SELECT DISTINCT motor_pump as name
      FROM processed_data
      WHERE motor_pump IS NOT NULL
      ORDER BY motor_pump ASC
    `;
    
    const result = await query(sql);
    const machines = result.rows.map(row => row.name);
    
    return res.json({ 
      success: true, 
      machines,
      count: machines.length 
    });
  } catch (error) {
    console.error('Erro ao buscar máquinas:', error);
    return res.status(500).json({ 
      success: false, 
      error: 'Erro ao buscar máquinas disponíveis' 
    });
  }
});

// Rota para buscar informações detalhadas de uma máquina específica
router.get('/machines/:machineName', requireAuth, async (req, res) => {
  try {
    const { machineName } = req.params;
    
    const sql = `
      SELECT 
        motor_pump,
        COUNT(*) as total_records,
        MIN(timestamp) as first_record,
        MAX(timestamp) as last_record
      FROM processed_data
      WHERE motor_pump = $1
      GROUP BY motor_pump
    `;
    
    const result = await query(sql, [machineName]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ 
        success: false, 
        error: 'Máquina não encontrada' 
      });
    }
    
    return res.json({ 
      success: true, 
      machine: result.rows[0] 
    });
  } catch (error) {
    console.error('Erro ao buscar informações da máquina:', error);
    return res.status(500).json({ 
      success: false, 
      error: 'Erro ao buscar informações da máquina' 
    });
  }
});

// Rota para buscar última predição de saúde de uma máquina
router.get('/machines/:machineName/health-prediction', /*requireAuth*/ async (req, res) => {
  try {
    const { machineName } = req.params;
    
    const sql = `
      SELECT 
        id,
        prediction,
        timestamp,
        motor_pump
      FROM predictions
      WHERE motor_pump = $1 AND model_type = 'gru'
      ORDER BY timestamp DESC
      LIMIT 1
    `;
    
    const result = await query(sql, [machineName]);
    
    if (result.rows.length === 0) {
      return res.json({ 
        success: true, 
        prediction: null,
        message: 'Nenhuma predição encontrada para esta máquina'
      });
    }
    
    const predictionData = result.rows[0];
    
    return res.json({ 
      success: true, 
      prediction: {
        id: predictionData.id,
        timestamp: predictionData.timestamp,
        motor_pump: predictionData.motor_pump,
        ...predictionData.prediction
      }
    });
  } catch (error) {
    console.error('Erro ao buscar predição de saúde:', error);
    return res.status(500).json({ 
      success: false, 
      error: 'Erro ao buscar predição de saúde' 
    });
  }
});

// Rota para buscar última predição de funcionamento (XGBoost) de uma máquina
router.get('/machines/:machineName/status-prediction', requireAuth, async (req, res) => {
  try {
    const { machineName } = req.params;
    
    // Buscar predições que contenham 'results' (indicador de predição XGBoost)
    const sql = `
      SELECT 
        id,
        prediction,
        timestamp,
        motor_pump
      FROM predictions
      WHERE motor_pump = $1
        AND prediction->>'results' IS NOT NULL
      ORDER BY timestamp DESC
      LIMIT 1
    `;
    
    const result = await query(sql, [machineName]);
    
    if (result.rows.length === 0) {
      return res.json({ 
        success: true, 
        prediction: null,
        message: 'Nenhuma predição de status encontrada para esta máquina'
      });
    }
    
    const predictionData = result.rows[0];
    const predictionJson = predictionData.prediction;
    
    // Extrair o primeiro resultado (sample 1)
    const firstResult = predictionJson.results && predictionJson.results[0];
    
    return res.json({ 
      success: true, 
      prediction: {
        id: predictionData.id,
        timestamp: predictionData.timestamp,
        motor_pump: predictionData.motor_pump,
        prediction: firstResult?.prediction || 0,
        status: firstResult?.status || 'UNKNOWN',
        probability_normal: firstResult?.probability_normal || 0,
        probability_pre_failure: firstResult?.probability_pre_failure || 0,
        risk_level: firstResult?.risk_level || 'UNKNOWN',
        total_samples: predictionJson.total_samples || 0,
        alerts_detected: predictionJson.alerts_detected || 0
      }
    });
  } catch (error) {
    console.error('Erro ao buscar predição de status:', error);
    return res.status(500).json({ 
      success: false, 
      error: 'Erro ao buscar predição de status' 
    });
  }
});

export default router;
