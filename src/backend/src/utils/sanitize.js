export function assertValidIdentifier(identifier, label = 'identifier') {
  if (typeof identifier !== 'string') {
    throw new Error(`${label} must be a string`);
  }
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(identifier)) {
    throw new Error(`Invalid ${label}`);
  }
  return identifier;
}


