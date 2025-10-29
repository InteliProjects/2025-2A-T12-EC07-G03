import dotenv from 'dotenv';

dotenv.config();

const strToBool = (v, defaultValue = false) => {
  if (v === undefined || v === null || v === '') return defaultValue;
  return ['1', 'true', 'yes', 'on'].includes(String(v).toLowerCase());
};

export const env = {
  NODE_ENV: process.env.NODE_ENV || 'development',
  PORT: process.env.PORT || '4000',

  // CORS
  CORS_ORIGINS: process.env.CORS_ORIGINS || '',

  // JWT
  JWT_SECRET: process.env.JWT_SECRET || 'change_me',
  JWT_EXPIRES_IN: process.env.JWT_EXPIRES_IN || '7d',

  // Postgres
  DATABASE_URL: process.env.DATABASE_URL,
  PGHOST: process.env.PGHOST,
  PGPORT: process.env.PGPORT || '5432',
  PGDATABASE: process.env.PGDATABASE,
  PGUSER: process.env.PGUSER,
  PGPASSWORD: process.env.PGPASSWORD,
  PGSSL: strToBool(process.env.PGSSL, false),
  PGSSL_REJECT_UNAUTHORIZED: strToBool(
    process.env.PGSSL_REJECT_UNAUTHORIZED,
    false
  ),

  // Auth
  USERS_TABLE: process.env.USERS_TABLE || 'users',

  // MQTT
  HOST_IP: process.env.HOST_IP || 'localhost',
  HOST_PORT: process.env.HOST_PORT || '1883',
  MQTT_USERNAME: process.env.MQTT_USERNAME,
  MQTT_PASSWORD: process.env.MQTT_PASSWORD,
  DISCOVERY_TIMEOUT: process.env.DISCOVERY_TIMEOUT || '900',
  LOG_DIRECTORY: process.env.LOG_DIRECTORY || './logs',
  LOG_INTERVAL_MINUTES: process.env.LOG_INTERVAL_MINUTES || '10',
  MQTT_TLS: strToBool(process.env.MQTT_TLS, false),
};

