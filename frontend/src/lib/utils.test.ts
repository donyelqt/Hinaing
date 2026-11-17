import { describe, it, expect } from 'vitest';

import { cn } from './utils';

describe('cn', () => {
  it('joins class names', () => {
    expect(cn('a', 'b')).toBe('a b');
  });

  it('drops falsy inputs', () => {
    expect(cn('a', false, null, undefined, 'b')).toBe('a b');
  });

  it('merges conflicting tailwind spacing, last wins', () => {
    expect(cn('p-2', 'p-3')).toBe('p-3');
    expect(cn('text-slate-700', 'text-violet-600')).toBe('text-violet-600');
  });
});
