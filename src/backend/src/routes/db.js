import { Router } from 'express';
import format from 'pg-format';
import { z } from 'zod';
import { requireAuth } from '../middleware/auth.js';
import { query } from '../services/db.js';
import { assertValidIdentifier } from '../utils/sanitize.js';

const router = Router();

router.get('/tables', requireAuth, async (_req, res) => {
  try {
    const result = await query(
      `SELECT table_schema, table_name
       FROM information_schema.tables
       WHERE table_type = 'BASE TABLE' AND table_schema NOT IN ('pg_catalog', 'information_schema')
       ORDER BY table_schema, table_name`
    );
    res.json({ tables: result.rows });
  } catch (err) {
    res.status(500).json({ error: 'Failed to list tables' });
  }
});

export default router;

router.get('/columns/:schema/:table', requireAuth, async (req, res) => {
  try {
    const schema = assertValidIdentifier(req.params.schema, 'schema');
    const table = assertValidIdentifier(req.params.table, 'table');
    const result = await query(
      `SELECT column_name, data_type
       FROM information_schema.columns
       WHERE table_schema = $1 AND table_name = $2
       ORDER BY ordinal_position`,
      [schema, table]
    );
    res.json({ schema, table, columns: result.rows });
  } catch (err) {
    res.status(400).json({ error: err.message || 'Failed to list columns' });
  }
});

router.get('/table/:schema/:table', requireAuth, async (req, res) => {
  try {
    const schema = assertValidIdentifier(req.params.schema, 'schema');
    const table = assertValidIdentifier(req.params.table, 'table');
    const limitSchema = z.coerce.number().int().min(1).max(200).catch(50);
    const limit = limitSchema.parse(req.query.limit);
    const sql = format('SELECT * FROM %I.%I LIMIT %L', schema, table, limit);
    const result = await query(sql);
    res.json({ schema, table, count: result.rowCount, rows: result.rows });
  } catch (err) {
    res.status(400).json({ error: err.message || 'Failed to fetch table' });
  }
});


