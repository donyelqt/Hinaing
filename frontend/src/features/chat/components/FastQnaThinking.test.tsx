import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { FastQnaThinking } from './FastQnaThinking';

const markup = (phase: Parameters<typeof FastQnaThinking>[0]['phase']) =>
  renderToStaticMarkup(<FastQnaThinking phase={phase} />);

describe('FastQnaThinking', () => {
  it('is hidden from assistive tech because the answer is the status message', () => {
    const html = markup({ kind: 'retrieval', progress: 0.4 });
    expect(html).toContain('aria-hidden="true"');
    expect(html).not.toContain('aria-live');
    expect(html).not.toContain('role="status"');
  });

  it('names the phase it is in so the two passes are distinguishable', () => {
    expect(markup({ kind: 'retrieval', progress: 0.4 })).toContain('data-phase="retrieval"');
    expect(markup({ kind: 'generating', progress: 0.8 })).toContain('data-phase="generating"');
  });

  it('labels the pass that is actually running', () => {
    expect(markup({ kind: 'retrieval', progress: 0.4 })).toContain('Searching for relevant information');
    expect(markup({ kind: 'generating', progress: 0.8 })).toContain('Generating response');
  });

  it('renders an orb and a halo, never a progress bar', () => {
    const html = markup({ kind: 'retrieval', progress: 0.4 });
    expect(html).toContain('blur-[6px]');
    expect(html).not.toContain('scaleX(');
  });

  it('drives every layer from motion-safe so reduced motion gets a still frame', () => {
    const html = markup({ kind: 'retrieval', progress: 0.4 });
    expect(html.match(/motion-safe:animate-\[/g)).toHaveLength(3);
  });

  it('kills all three animations under reduced motion', () => {
    const html = markup({ kind: 'retrieval', progress: 0.4 });
    expect(html).toContain('.fq-orb, .fq-orb-halo, .fq-orb-label { animation: none !important; }');
  });

  it('keeps an orb silhouette when motion is reduced, not the raw square', () => {
    const html = markup({ kind: 'retrieval', progress: 0.4 });
    expect(html).toContain('.fq-orb { border-radius: 58% 42% 55% 45% / 45% 58% 42% 55%; }');
    expect(html).toContain('.fq-orb-halo { opacity: 0.26; }');
  });

  it('carries the label light as a clipped gradient rather than a colour change', () => {
    const html = markup({ kind: 'retrieval', progress: 0.4 });
    expect(html).toContain('background-clip:text');
    expect(html).toContain('-webkit-text-fill-color:transparent');
  });

  it('reserves a full row so the answer below does not shift when it unmounts', () => {
    const html = markup({ kind: 'retrieval', progress: 0.4 });
    expect(html).toContain('min-h-11');
  });
});