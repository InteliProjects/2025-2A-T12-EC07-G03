import pg from 'pg';
import { env } from '../utils/env.js';

const { Pool } = pg;

const ssl = env.PGSSL ? { rejectUnauthorized: env.PGSSL_REJECT_UNAUTHORIZED } : false;

const baseConfig = env.DATABASE_URL
  ? { connectionString: env.DATABASE_URL, ssl }
  : {
      host: env.PGHOST,
      port: Number(env.PGPORT || 5432),
      database: env.PGDATABASE,
      user: env.PGUSER,
      password: env.PGPASSWORD,
      ssl,
    };

export const pool = new Pool({
  ...baseConfig,
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 10000,
});

pool.on('error', (err) => {
  // eslint-disable-next-line no-console
  console.error('Unexpected PG pool error', err);
});

export const query = (text, params) => pool.query(text, params);

export const withClient = async (fn) => {
  const client = await pool.connect();
  try {
    return await fn(client);
  } finally {
    client.release();
  }
};


