import express from 'express';
import { getMQTTService } from '../services/mqtt.js';

const router = express.Router();

// Obter dados de todas as máquinas
router.get('/machines', (req, res) => {
  try {
    const mqttService = getMQTTService();
    const machines = mqttService.getAllMachinesData();
    res.json(machines);
  } catch (error) {
    console.error('Erro ao obter dados das máquinas:', error);
    res.status(500).json({ error: 'Erro interno do servidor' });
  }
});

// Obter dados de uma máquina específica
router.get('/machines/:machineId', (req, res) => {
  try {
    const { machineId } = req.params;
    const mqttService = getMQTTService();
    const machine = mqttService.getMachineData(machineId);
    
    if (!machine) {
      return res.status(404).json({ error: 'Máquina não encontrada' });
    }
    
    res.json(machine);
  } catch (error) {
    console.error('Erro ao obter dados da máquina:', error);
    res.status(500).json({ error: 'Erro interno do servidor' });
  }
});

// Obter resumo do dashboard
router.get('/dashboard/summary', (req, res) => {
  try {
    const mqttService = getMQTTService();
    const summary = mqttService.getDashboardSummary();
    res.json(summary);
  } catch (error) {
    console.error('Erro ao obter resumo do dashboard:', error);
    res.status(500).json({ error: 'Erro interno do servidor' });
  }
});

// Status da conexão MQTT
router.get('/mqtt/status', (req, res) => {
  try {
    const mqttService = getMQTTService();
    res.json({
      connected: mqttService.isConnected,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Erro ao obter status MQTT:', error);
    res.status(500).json({ error: 'Erro interno do servidor' });
  }
});

export default router;