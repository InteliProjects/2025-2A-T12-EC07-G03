import { Router } from 'express';
import { query } from '../services/db.js';
import { requireAuth } from '../middleware/auth.js';

const router = Router();

// Rota para buscar modelos disponíveis
router.get('/', requireAuth, async (req, res) => {
  try {
    const sql = `
      SELECT 
        id,
        machine_name,
        bucket_address,
        data_start_date,
        data_end_date,
        metrics,
        timestamp as created_at
      FROM models
      ORDER BY timestamp DESC
    `;
    
    const result = await query(sql);
    
    // Processar métricas para cada modelo
    const models = result.rows.map(model => {
      const metrics = model.metrics || {};
      const classificationReport = metrics.classification_report || {};
      
      // Extrair métricas principais
      const accuracy = classificationReport.accuracy || 0;
      const weightedAvg = classificationReport['weighted avg'] || {};
      
      return {
        id: model.id,
        machine_name: model.machine_name,
        bucket_address: model.bucket_address,
        data_start_date: model.data_start_date,
        data_end_date: model.data_end_date,
        created_at: model.created_at,
        type: 'XGBoost', // Por enquanto só temos XGBoost
        indicator: 'Funcionamento', // XGBoost é para indicador de funcionamento
        metrics: {
          accuracy: (accuracy * 100).toFixed(2),
          precision: ((weightedAvg.precision || 0) * 100).toFixed(2),
          recall: ((weightedAvg.recall || 0) * 100).toFixed(2),
          f1_score: ((weightedAvg['f1-score'] || 0) * 100).toFixed(2),
          auc_score: ((metrics.auc_score || 0) * 100).toFixed(2)
        },
        raw_metrics: metrics
      };
    });
    
    return res.json({ 
      success: true, 
      models,
      count: models.length 
    });
  } catch (error) {
    console.error('Erro ao buscar modelos:', error);
    return res.status(500).json({ 
      success: false, 
      error: 'Erro ao buscar modelos disponíveis' 
    });
  }
});

// Rota para buscar um modelo específico
router.get('/:modelId', requireAuth, async (req, res) => {
  try {
    const { modelId } = req.params;
    
    const sql = `
      SELECT 
        id,
        machine_name,
        bucket_address,
        data_start_date,
        data_end_date,
        metrics,
        timestamp as created_at
      FROM models
      WHERE id = $1
    `;
    
    const result = await query(sql, [modelId]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ 
        success: false, 
        error: 'Modelo não encontrado' 
      });
    }
    
    const model = result.rows[0];
    const metrics = model.metrics || {};
    const classificationReport = metrics.classification_report || {};
    const accuracy = classificationReport.accuracy || 0;
    const weightedAvg = classificationReport['weighted avg'] || {};
    
    return res.json({ 
      success: true, 
      model: {
        id: model.id,
        machine_name: model.machine_name,
        bucket_address: model.bucket_address,
        data_start_date: model.data_start_date,
        data_end_date: model.data_end_date,
        created_at: model.created_at,
        type: 'XGBoost',
        indicator: 'Funcionamento',
        metrics: {
          accuracy: (accuracy * 100).toFixed(2),
          precision: ((weightedAvg.precision || 0) * 100).toFixed(2),
          recall: ((weightedAvg.recall || 0) * 100).toFixed(2),
          f1_score: ((weightedAvg['f1-score'] || 0) * 100).toFixed(2),
          auc_score: ((metrics.auc_score || 0) * 100).toFixed(2)
        },
        raw_metrics: metrics
      }
    });
  } catch (error) {
    console.error('Erro ao buscar modelo:', error);
    return res.status(500).json({ 
      success: false, 
      error: 'Erro ao buscar modelo' 
    });
  }
});

// Rota para buscar o melhor modelo por máquina (baseado em F1-Score)
router.get('/best/:machineName', requireAuth, async (req, res) => {
  try {
    const { machineName } = req.params;
    
    const sql = `
      SELECT 
        id,
        machine_name,
        bucket_address,
        data_start_date,
        data_end_date,
        metrics,
        timestamp as created_at
      FROM models
      WHERE machine_name = $1
      ORDER BY 
        (metrics->'classification_report'->'weighted avg'->>'f1-score')::float DESC,
        timestamp DESC
      LIMIT 1
    `;
    
    const result = await query(sql, [machineName]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ 
        success: false, 
        error: 'Nenhum modelo encontrado para esta máquina' 
      });
    }
    
    const model = result.rows[0];
    const metrics = model.metrics || {};
    const classificationReport = metrics.classification_report || {};
    const accuracy = classificationReport.accuracy || 0;
    const weightedAvg = classificationReport['weighted avg'] || {};
    
    return res.json({ 
      success: true, 
      model: {
        id: model.id,
        machine_name: model.machine_name,
        bucket_address: model.bucket_address,
        data_start_date: model.data_start_date,
        data_end_date: model.data_end_date,
        created_at: model.created_at,
        type: 'XGBoost',
        indicator: 'Funcionamento',
        metrics: {
          accuracy: (accuracy * 100).toFixed(2),
          precision: ((weightedAvg.precision || 0) * 100).toFixed(2),
          recall: ((weightedAvg.recall || 0) * 100).toFixed(2),
          f1_score: ((weightedAvg['f1-score'] || 0) * 100).toFixed(2),
          auc_score: ((metrics.auc_score || 0) * 100).toFixed(2)
        },
        raw_metrics: metrics
      }
    });
  } catch (error) {
    console.error('Erro ao buscar melhor modelo:', error);
    return res.status(500).json({ 
      success: false, 
      error: 'Erro ao buscar melhor modelo' 
    });
  }
});

// Rota para excluir um modelo
router.delete('/:modelId', requireAuth, async (req, res) => {
  try {
    const { modelId } = req.params;
    
    // Verificar se o modelo existe
    const checkSql = `SELECT id FROM models WHERE id = $1`;
    const checkResult = await query(checkSql, [modelId]);
    
    if (checkResult.rows.length === 0) {
      return res.status(404).json({ 
        success: false, 
        error: 'Modelo não encontrado' 
      });
    }
    
    // Excluir o modelo
    const deleteSql = `DELETE FROM models WHERE id = $1`;
    await query(deleteSql, [modelId]);
    
    return res.json({ 
      success: true, 
      message: 'Modelo excluído com sucesso' 
    });
  } catch (error) {
    console.error('Erro ao excluir modelo:', error);
    return res.status(500).json({ 
      success: false, 
      error: 'Erro ao excluir modelo' 
    });
  }
});

// Rota para buscar modelos GRU por máquina
router.get('/gru/:machineName', requireAuth, async (req, res) => {
  try {
    const { machineName } = req.params;
    
    const sql = `
      SELECT 
        id,
        machine_name,
        bucket_address,
        data_start_date,
        data_end_date,
        metrics,
        timestamp as created_at,
        model_type
      FROM models
      WHERE model_type = 'gru' 
        AND machine_name = $1
      ORDER BY timestamp DESC
    `;
    
    const result = await query(sql, [machineName]);
    
    const models = result.rows.map(model => ({
      id: model.id,
      machine_name: model.machine_name,
      bucket_address: model.bucket_address,
      data_start_date: model.data_start_date,
      data_end_date: model.data_end_date,
      created_at: model.created_at,
      model_type: model.model_type,
      metrics: model.metrics
    }));
    
    return res.json({ 
      success: true, 
      models,
      count: models.length 
    });
  } catch (error) {
    console.error('Erro ao buscar modelos GRU:', error);
    return res.status(500).json({ 
      success: false, 
      error: 'Erro ao buscar modelos GRU' 
    });
  }
});

export default router;