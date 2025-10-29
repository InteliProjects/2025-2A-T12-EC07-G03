import bcrypt from 'bcryptjs';
import { pool, query } from '../src/services/db.js';
import format from 'pg-format';
import { env } from '../src/utils/env.js';
import { assertValidIdentifier } from '../src/utils/sanitize.js';

const toBool = (v) => ['1', 'true', 'yes', 'on'].includes(String(v || '').toLowerCase());

async function createUsersTable(usersTable) {
  const sql = format(
    'CREATE TABLE IF NOT EXISTS %I (id SERIAL PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, name TEXT, created_at TIMESTAMPTZ DEFAULT now())',
    usersTable
  );
  await query(sql);
}

async function ensureAdminUser(usersTable) {
  const adminEmail = process.env.ADMIN_EMAIL;
  const adminPassword = process.env.ADMIN_PASSWORD;
  const adminName = process.env.ADMIN_NAME || 'Admin';
  const overwrite = toBool(process.env.ADMIN_OVERWRITE_PASSWORD || 'false');

  if (!adminEmail || !adminPassword) {
    // No admin seed requested
    return { seeded: false };
  }

  const existing = await query(
    format('SELECT id FROM %I WHERE email = $1 LIMIT 1', usersTable),
    [adminEmail]
  );

  if (existing.rows.length === 0) {
    const salt = await bcrypt.genSalt(10);
    const hash = await bcrypt.hash(adminPassword, salt);
    const inserted = await query(
      format('INSERT INTO %I (email, password_hash, name) VALUES ($1, $2, $3) RETURNING id, email, name, created_at', usersTable),
      [adminEmail, hash, adminName]
    );
    return { seeded: true, action: 'created', user: inserted.rows[0] };
  }

  if (overwrite) {
    const salt = await bcrypt.genSalt(10);
    const hash = await bcrypt.hash(adminPassword, salt);
    await query(
      format('UPDATE %I SET password_hash = $1, name = $2 WHERE email = $3', usersTable),
      [hash, adminName, adminEmail]
    );
    return { seeded: true, action: 'updated', email: adminEmail };
  }

  return { seeded: false, action: 'skipped_exists', email: adminEmail };
}

async function main() {
  const usersTable = assertValidIdentifier(env.USERS_TABLE || 'users', 'USERS_TABLE');
  // eslint-disable-next-line no-console
  console.log(`Using users table: ${usersTable}`);
  await createUsersTable(usersTable);
  // eslint-disable-next-line no-console
  console.log('Users table ensured.');

  const seed = await ensureAdminUser(usersTable);
  // eslint-disable-next-line no-console
  console.log('Admin seed result:', seed);
}

main()
  .then(async () => {
    await pool.end();
    process.exit(0);
  })
  .catch(async (err) => {
    // eslint-disable-next-line no-console
    console.error('Setup failed:', err);
    try { await pool.end(); } catch {}
    process.exit(1);
  });


