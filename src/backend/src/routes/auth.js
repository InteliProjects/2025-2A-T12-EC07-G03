import { Router } from 'express';
import bcrypt from 'bcryptjs';
import format from 'pg-format';
import { z } from 'zod';
import { query } from '../services/db.js';
import { env } from '../utils/env.js';
import { signToken } from '../services/jwt.js';
import { requireAuth } from '../middleware/auth.js';

const router = Router();

const USERS_TABLE = env.USERS_TABLE;

const registerSchema = z.object({
  email: z.string().email().max(254),
  password: z.string().min(8).max(128),
  name: z.string().max(200).optional().nullable(),
});

router.post('/register', async (req, res) => {
  try {
    const parsed = registerSchema.safeParse(req.body || {});
    if (!parsed.success) {
      return res.status(400).json({ error: 'Invalid payload' });
    }
    const email = String(parsed.data.email).trim().toLowerCase();
    const name = parsed.data.name ?? null;
    const password = parsed.data.password;

    const selectUserSql = format('SELECT id FROM %I WHERE email = $1 LIMIT 1', USERS_TABLE);
    const existing = await query(selectUserSql, [email]);
    if (existing.rows.length > 0) {
      return res.status(409).json({ error: 'Email already registered' });
    }
    const salt = await bcrypt.genSalt(10);
    const hash = await bcrypt.hash(password, salt);
    const insertSql = format(
      'INSERT INTO %I (email, password, name) VALUES ($1, $2, $3) RETURNING id, email, name',
      USERS_TABLE
    );
    const insert = await query(insertSql, [email, hash, name]);
    const user = insert.rows[0];
    const token = signToken({ sub: user.id, email: user.email });
    return res.status(201).json({ user, token });
  } catch (err) {
    return res.status(500).json({ error: 'Registration failed' });
  }
});

const loginSchema = z.object({
  email: z.string().email().max(254),
  password: z.string().min(8).max(128),
});

router.post('/login', async (req, res) => {
  try {
    const parsed = loginSchema.safeParse(req.body || {});
    if (!parsed.success) {
      return res.status(400).json({ error: 'Invalid payload' });
    }
    const email = String(parsed.data.email).trim().toLowerCase();
    const password = parsed.data.password;

    const selectSql = format(
      'SELECT id, email, password, name FROM %I WHERE email = $1 LIMIT 1',
      USERS_TABLE
    );
    const result = await query(selectSql, [email]);
    if (result.rows.length === 0) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    const user = result.rows[0];
    // Suporta tanto 'password' quanto 'password_hash' para compatibilidade
    const passwordHash = user.password_hash || user.password;
    const ok = await bcrypt.compare(password, passwordHash);
    if (!ok) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    const token = signToken({ sub: user.id, email: user.email });
    delete user.password_hash;
    delete user.password;
    return res.json({ user, token });
  } catch (err) {
    return res.status(500).json({ error: 'Login failed' });
  }
});

export default router;

router.get('/me', requireAuth, (req, res) => {
  const user = req.user || null;
  res.json({ user });
});


