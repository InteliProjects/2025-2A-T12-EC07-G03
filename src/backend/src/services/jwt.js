import jwt from 'jsonwebtoken';
import { env } from '../utils/env.js';

export function signToken(payload, options = {}) {
  const base = {
    expiresIn: env.JWT_EXPIRES_IN,
    issuer: 'app-backend',
    audience: 'app-frontend',
  };
  return jwt.sign(payload, env.JWT_SECRET, { ...base, ...options });
}

export function verifyToken(token) {
  return jwt.verify(token, env.JWT_SECRET, {
    issuer: 'app-backend',
    audience: 'app-frontend',
  });
}


