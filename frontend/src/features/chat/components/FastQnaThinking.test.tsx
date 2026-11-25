import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { FastQnaThinking } from './FastQnaThinking';

const markup = () => renderToStaticMarkup(<FastQnaThinking />);

describe('FastQnaThinking', () => {
  it('is hidden from assistive tech because the answer is the status message', () => {
    const html = markup();
    expect(html).toContain('aria-hidden="true"');
    expect(html).not.toContain('aria-live');
    expect(html).not.toContain('role="status"');
  });

  it('shows Thinking from the first frame so the wait is never blank', () => {
    const html = markup();
    expect(html).toContain('Thinking');
    expect(html).toContain('class="fq-orb-label');
  });

  it('never names a pass, so the row cannot change width mid-wait', () => {
    const html = markup();
    expect(html).not.toContain('Searching for relevant');
    expect(html).not.toContain('Generating response');
    expect(html).not.toContain('Starting');
  });

  it('renders a lit sphere, never a progress bar', () => {
    const html = markup();
    expect(html).toContain('radial-gradient(circle at 30% 24%');
    expect(html).not.toContain('scaleX(');
    expect(html).not.toContain('blur-[6px]');
  });

  it('keeps the sheen on the rim with a mask instead of across the face', () => {
    const html = markup();
    expect(html).toContain('mask-image:radial-gradient(farthest-side');
    expect(html).toContain('conic-gradient(from 0deg');
  });

  it('drives every animated layer from motion-safe', () => {
    const html = markup();
    expect(html.match(/motion-safe:animate-\[/g)).toHaveLength(5);
  });

  it('kills every animation under reduced motion', () => {
    const html = markup();
    expect(html).toContain('.fq-orb, .fq-orb-core, .fq-orb-sheen, .fq-orb-bloom, .fq-orb-label { animation: none !important; }');
  });

  it('holds a lit sphere when motion is reduced, not an unstyled box', () => {
    const html = markup();
    expect(html).toContain('.fq-orb-bloom { opacity: 0.34; }');
    expect(html).toContain('rounded-full');
    expect(html).toContain('radial-gradient(circle at 30% 24%');
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