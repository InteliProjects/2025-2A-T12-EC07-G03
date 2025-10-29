import express from 'express';
import { query } from '../services/db.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

// GET /api/training-jobs - Retorna os jobs de treinamento
router.get('/', requireAuth, async (req, res) => {
  try {
    const sql = `
      SELECT 
        id,
        machine_name,
        indicator,
        status,
        error_message,
        created_at,
        updated_at,
        start_date,
        end_date,
        finished_at,
        bucket_address
      FROM training_jobs
      ORDER BY created_at DESC
      LIMIT 50
    `;
    
    const result = await query(sql);
    
    return res.json({
      success: true,
      jobs: result.rows,
      count: result.rows.length
    });
  } catch (error) {
    console.error('Erro ao buscar training jobs:', error);
    return res.status(500).json({
      success: false,
      error: 'Erro ao buscar jobs de treinamento'
    });
  }
});

// GET /api/training-jobs/:id - Retorna um job específico
router.get('/:id', requireAuth, async (req, res) => {
  try {
    const { id } = req.params;
    
    const sql = `
      SELECT 
        id,
        machine_name,
        indicator,
        status,
        error_message,
        created_at,
        updated_at,
        start_date,
        end_date,
        finished_at,
        bucket_address
      FROM training_jobs
      WHERE id = $1
    `;
    
    const result = await query(sql, [id]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'Job não encontrado'
      });
    }
    
    return res.json({
      success: true,
      job: result.rows[0]
    });
  } catch (error) {
    console.error('Erro ao buscar training job:', error);
    return res.status(500).json({
      success: false,
      error: 'Erro ao buscar job de treinamento'
    });
  }
});

export default router;
