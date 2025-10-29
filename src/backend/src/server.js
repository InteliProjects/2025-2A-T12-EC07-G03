import { createServer } from 'node:http';
import { Server } from 'socket.io';
import app from './app.js';
import { env } from './utils/env.js';
import { pool } from './services/db.js';
import { getMQTTService } from './services/mqtt.js';
import autoPredictionService from './services/autoPrediction.js';

const port = Number(env.PORT || 4000);

const server = createServer(app);

// Initialize Socket.IO
const io = new Server(server, {
  cors: {
    origin: (env.CORS_ORIGINS || '').split(',').map(o => o.trim()).filter(Boolean),
    methods: ['GET', 'POST']
  }
});

// Handle WebSocket connections
io.on('connection', (socket) => {
  socket.on('disconnect', () => {});
  
  // Send initial data when client connects
  const mqttService = getMQTTService();
  const initialData = {
    machines: mqttService.getAllMachinesData(),
    summary: mqttService.getDashboardSummary(),
    mqttStatus: { connected: mqttService.isConnected }
  };
  
  socket.emit('initialData', initialData);
  
  // Also trigger periodic emission when new client connects
  mqttService.emitInitialData();
});

server.listen(port, async () => {
  // Test DB connectivity on boot
  try {
    await pool.query('SELECT 1');
    // eslint-disable-next-line no-console
    console.log(`DB connected. Server listening on http://localhost:${port}`);
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('Server started but DB connection failed:', err.message);
  }

  // Initialize MQTT service with WebSocket integration
  try {
    const mqttService = getMQTTService();
    
    // Pass the Socket.IO instance to MQTT service for real-time updates
    mqttService.setSocketIO(io);
    
    mqttService.connect();
  } catch (err) {
    console.error('Failed to initialize MQTT service:', err.message);
  }

  // Initialize Auto Prediction Service
  try {
    console.log('\n Iniciando serviço de predições automáticas...');
    autoPredictionService.start();
  } catch (err) {
    console.error('Failed to initialize Auto Prediction service:', err.message);
  }
});

const shutdown = async (signal) => {
  // eslint-disable-next-line no-console
  console.log(`\n${signal} received. Shutting down...`);
  try {
    // Stop Auto Prediction service
    autoPredictionService.stop();
    
    // Disconnect MQTT service
    const mqttService = getMQTTService();
    mqttService.disconnect();
    
    await pool.end();
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('Error during shutdown', err);
  }
  server.close(() => process.exit(0));
};

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));

