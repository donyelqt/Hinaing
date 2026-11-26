import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { FastQnaThinking } from './FastQnaThinking';

const markup = (stage?: Parameters<typeof FastQnaThinking>[0]['stage']) =>
  renderToStaticMarkup(<FastQnaThinking stage={stage} />);

describe('FastQnaThinking', () => {
  it('is hidden from assistive tech because the answer is the status message', () => {
    const html = markup();
    expect(html).toContain('aria-hidden="true"');
    expect(html).not.toContain('aria-live');
    expect(html).not.toContain('role="status"');
  });

  it('says Thinking by default so the wait is never blank', () => {
    const html = markup();
    expect(html).toContain('Thinking');
    expect(html).toContain('data-stage="thinking"');
    expect(html).toContain('class="fq-orb-label');
  });

  it('names each pass so the user can see the request move', () => {
    expect(markup('retrieval')).toContain('Searching for relevant information');
    expect(markup('generating')).toContain('Generating response');
    expect(markup('retrieval')).toContain('data-stage="retrieval"');
    expect(markup('generating')).toContain('data-stage="generating"');
  });

  it('renders hard cel bands, not a smooth falloff', () => {
    const html = markup();
    expect(html).toContain('#ffffff 26%');
    expect(html).toContain('rgb(var(--brand-to-rgb)) 27%');
    expect(html).toContain('rgb(30 27 75) 100%');
    expect(html).not.toContain('scaleX(');
    expect(html).not.toContain('blur-[');
  });

  it('draws a sharp crescent instead of a soft inner glow', () => {
    const html = markup();
    expect(html).toContain('rgba(255,255,255,0.92) 53%');
    expect(html).toContain('rgba(255,255,255,0) 63%');
  });

  it('steps the crescent rather than easing it, which is the cel tell', () => {
    const html = markup();
    expect(html).toContain('steps(1,end)');
  });

  it('carries a bright keyline on the rim', () => {
    const html = markup();
    expect(html).toContain('conic-gradient(from 210deg');
    expect(html).toContain('mask-image:radial-gradient(farthest-side');
  });

  it('drives every animated layer from motion-safe', () => {
    const html = markup();
    expect(html.match(/motion-safe:animate-\[/g)).toHaveLength(4);
  });

  it('kills every animation under reduced motion', () => {
    const html = markup();
    expect(html).toContain('.fq-orb, .fq-orb-crescent, .fq-orb-keyline, .fq-orb-halo, .fq-orb-label { animation: none !important; }');
  });

  it('holds a drawn orb when motion is reduced, not an unstyled box', () => {
    const html = markup();
    expect(html).toContain('.fq-orb-halo { opacity: 0.4; }');
    expect(html).toContain('rounded-full');
    expect(html).toContain('#ffffff 26%');
  });

  it('carries the label light as a clipped gradient rather than a colour change', () => {
    const html = markup();
    expect(html).toContain('background-clip:text');
    expect(html).toContain('-webkit-text-fill-color:transparent');
  });

  it('reserves a full row so the answer below does not shift when it unmounts', () => {
    const html = markup();
    expect(html).toContain('min-h-11');
  });
});