import { Router } from 'express';
import autoPredictionService from '../services/autoPrediction.js';

const router = Router();

/**
 * Rota para iniciar o serviço de predições automáticas
 */
router.post('/start', async (req, res) => {
  try {
    const status = autoPredictionService.getStatus();
    
    if (status.isRunning) {
      return res.json({
        success: false,
        message: 'Serviço de predições automáticas já está em execução',
        status
      });
    }
    
    autoPredictionService.start();
    
    return res.json({
      success: true,
      message: 'Serviço de predições automáticas iniciado com sucesso',
      status: autoPredictionService.getStatus()
    });
  } catch (error) {
    console.error('Erro ao iniciar serviço de predições:', error);
    return res.status(500).json({
      success: false,
      error: 'Erro ao iniciar serviço de predições automáticas'
    });
  }
});

/**
 * Rota para parar o serviço de predições automáticas
 */
router.post('/stop', async (req, res) => {
  try {
    const status = autoPredictionService.getStatus();
    
    if (!status.isRunning) {
      return res.json({
        success: false,
        message: 'Serviço de predições automáticas não está em execução',
        status
      });
    }
    
    autoPredictionService.stop();
    
    return res.json({
      success: true,
      message: 'Serviço de predições automáticas parado com sucesso',
      status: autoPredictionService.getStatus()
    });
  } catch (error) {
    console.error('Erro ao parar serviço de predições:', error);
    return res.status(500).json({
      success: false,
      error: 'Erro ao parar serviço de predições automáticas'
    });
  }
});

/**
 * Rota para verificar o status do serviço
 */
router.get('/status', async (req, res) => {
  try {
    const status = autoPredictionService.getStatus();
    
    return res.json({
      success: true,
      status
    });
  } catch (error) {
    console.error('Erro ao verificar status:', error);
    return res.status(500).json({
      success: false,
      error: 'Erro ao verificar status do serviço'
    });
  }
});

/**
 * Rota para executar predições manualmente (sem esperar o intervalo)
 */
router.post('/run-now', async (req, res) => {
  try {
    // Executar predições de forma assíncrona
    autoPredictionService.runPredictions().catch(err => {
      console.error('Erro na execução manual de predições:', err);
    });
    
    return res.json({
      success: true,
      message: 'Execução de predições iniciada. Os resultados serão salvos no banco de dados.',
    });
  } catch (error) {
    console.error('Erro ao executar predições manualmente:', error);
    return res.status(500).json({
      success: false,
      error: 'Erro ao executar predições manualmente'
    });
  }
});

export default router;
