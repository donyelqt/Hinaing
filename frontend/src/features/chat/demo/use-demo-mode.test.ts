import { describe, it, expect } from 'vitest';

import { DEMO_MODE_STORAGE_KEY } from './use-demo-mode';

describe('demo mode config', () => {
  it('stores the flag under a stable key so reloads keep the choice', () => {
    expect(DEMO_MODE_STORAGE_KEY).toBe('hinaing:demo-mode');
  });

  it('reads only the exact on value, so a corrupt entry falls back to off', () => {
    const read = (raw: string | null): boolean => raw === 'on';
    expect(read('on')).toBe(true);
    expect(read('off')).toBe(false);
    expect(read(null)).toBe(false);
    expect(read('true')).toBe(false);
  });
});