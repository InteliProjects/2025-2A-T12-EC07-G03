import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import { env } from './utils/env.js';
import healthRouter from './routes/health.js';
import authRouter from './routes/auth.js';
import dbRouter from './routes/db.js';
import machinesRouter from './routes/machines.js';
import machinesDataRouter from './routes/machines_data.js';
import modelTrainingRouter from './routes/model_training.js';
import modelInferenceRouter from './routes/model_inference.js';
import trainingJobsRouter from './routes/training_jobs.js';
import modelsRouter from './routes/models.js';
import autoPredictionRouter from './routes/auto_prediction.js';

const app = express();

const corsOrigins = (env.CORS_ORIGINS || '').trim();

app.use(helmet());

// Se CORS_ORIGINS for '*', permite todas as origens
if (corsOrigins === '*') {
  app.use(
    cors({
      origin: true,
      credentials: true,
    })
  );
} else {
  // Caso contrário, usa lista específica de origens
  const allowedOrigins = corsOrigins
    .split(',')
    .map((o) => o.trim())
    .filter(Boolean);

  app.use(
    cors({
      origin: (origin, cb) => {
        if (!origin) return cb(null, true);
        if (allowedOrigins.length === 0 || allowedOrigins.includes(origin)) {
          return cb(null, true);
        }
        cb(new Error('CORS not allowed'));
      },
      credentials: true,
    })
  );
}
app.use(express.json({ limit: '1mb' }));
app.use(morgan('dev'));

app.use('/health', healthRouter);
app.use(
  '/auth',
  rateLimit({ windowMs: 15 * 60 * 1000, max: 100, standardHeaders: true, legacyHeaders: false }),
  authRouter
);
app.use('/db', dbRouter);
app.use('/api', machinesRouter);
app.use('/api/data', machinesDataRouter);
app.use('/model-training', modelTrainingRouter);
app.use('/model-inference', modelInferenceRouter);
app.use('/api/training-jobs', trainingJobsRouter);
app.use('/api/models', modelsRouter);
app.use('/api/auto-prediction', autoPredictionRouter);

app.get('/', (_req, res) => {
  res.json({ name: 'express-backend', status: 'ok' });
});

// Centralized error handler (last)
// eslint-disable-next-line no-unused-vars
app.use((err, _req, res, _next) => {
  const status = err.status || 500;
  const message = status >= 500 ? 'Internal Server Error' : err.message || 'Error';
  res.status(status).json({ error: message });
});

export default app;

