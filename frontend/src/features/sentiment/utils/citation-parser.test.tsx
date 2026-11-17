import { describe, it, expect } from 'vitest';

import { isEmptyParagraph, parseCitations, type CitationSource } from './citation-parser';

describe('isEmptyParagraph', () => {
  it('flags whitespace and punctuation-only paragraphs as empty', () => {
    expect(isEmptyParagraph('')).toBe(true);
    expect(isEmptyParagraph('   ')).toBe(true);
    expect(isEmptyParagraph('.. .')).toBe(true);
    expect(isEmptyParagraph("-–—*_'\"")).toBe(true);
  });

  it('flags paragraphs with real content as not empty', () => {
    expect(isEmptyParagraph('hi')).toBe(false);
    expect(isEmptyParagraph('. yes')).toBe(false);
  });
});

describe('parseCitations', () => {
  it('returns the original string when nothing matches', () => {
    const [out] = parseCitations('no citations here');
    expect(out).toBe('no citations here');
  });

  it('keeps ordinary paragraph text intact without citations', () => {
    const result = parseCitations('plain paragraph [not a citation]');
    expect(result).toEqual(['plain paragraph [not a citation]']);
  });

  it('numbers verified sources by domain order', () => {
    const sources: CitationSource[] = [{ url: 'https://www.phivolcs.dost.gov.ph' }, { url: 'https://inquirer.net/amp' }];
    const parts = parseCitations('fires rise [Src: phivolcs.dost.gov.ph | Sent: neutral | verified]', sources);
    expect(parts[0]).toContain('fires rise');
    const chip = parts.find((p): p is React.JSX.Element => typeof p !== 'string');
    expect(chip?.props['aria-label']).toContain('verified');
    expect(chip?.props['aria-label']).toContain('phivolcs.dost.gov.ph');
    expect(chip?.props.children).toBe(1);
  });

  it('unmapped statuses degrade to unverified rather than throw', () => {
    const parts = parseCitations('dot [Src: gmanetwork.com | Sent: neutral | skipped_limit]', []);
    const chip = parts.find((p): p is React.JSX.Element => typeof p !== 'string');
    expect(chip?.props['aria-label']).toContain('unverified');
  });
});
