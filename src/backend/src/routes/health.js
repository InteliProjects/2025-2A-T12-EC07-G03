import { Router } from 'express';
import { pool } from '../services/db.js';

const router = Router();

router.get('/', async (_req, res) => {
  const startedAt = Date.now();
  let db = 'ok';
  try {
    await pool.query('SELECT 1');
  } catch (err) {
    db = 'error';
  }
  res.json({
    status: 'ok',
    uptime: process.uptime(),
    responseMs: Date.now() - startedAt,
    db,
  });
});

export default router;


