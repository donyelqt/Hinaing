import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { FastQnaThinking } from './FastQnaThinking';

const markup = (phase?: Parameters<typeof FastQnaThinking>[0]['phase']) =>
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

  it('shows one label for both passes so the row never changes width', () => {
    const retrieval = markup({ kind: 'retrieval', progress: 0.4 });
    const generating = markup({ kind: 'generating', progress: 0.8 });
    expect(retrieval).toContain('Thinking');
    expect(generating).toContain('Thinking');
    expect(retrieval).not.toContain('Searching for relevant');
    expect(generating).not.toContain('Generating response');
  });

  it('shows the orb alone with no label while the request is still waiting', () => {
    const html = markup(undefined);
    expect(html).toContain('data-phase="pending"');
    expect(html).not.toContain('Starting');
    expect(html).not.toContain('class="fq-orb-label');
  });

  it('renders a lit sphere, never a progress bar', () => {
    const html = markup({ kind: 'retrieval', progress: 0.4 });
    expect(html).toContain('radial-gradient(circle at 30% 24%');
    expect(html).not.toContain('scaleX(');
    expect(html).not.toContain('blur-[6px]');
  });

  it('keeps the sheen on the rim with a mask instead of across the face', () => {
    const html = markup({ kind: 'retrieval', progress: 0.4 });
    expect(html).toContain('mask-image:radial-gradient(farthest-side');
    expect(html).toContain('conic-gradient(from 0deg');
  });

  it('drives every animated layer from motion-safe', () => {
    const html = markup({ kind: 'retrieval', progress: 0.4 });
    expect(html.match(/motion-safe:animate-\[/g)).toHaveLength(5);
  });

  it('kills every animation under reduced motion', () => {
    const html = markup({ kind: 'retrieval', progress: 0.4 });
    expect(html).toContain('.fq-orb, .fq-orb-core, .fq-orb-sheen, .fq-orb-bloom, .fq-orb-label { animation: none !important; }');
  });

  it('holds a lit sphere when motion is reduced, not an unstyled box', () => {
    const html = markup({ kind: 'retrieval', progress: 0.4 });
    expect(html).toContain('.fq-orb-bloom { opacity: 0.34; }');
    expect(html).toContain('rounded-full');
    expect(html).toContain('radial-gradient(circle at 30% 24%');
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