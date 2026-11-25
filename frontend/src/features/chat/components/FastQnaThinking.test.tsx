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

  it('keeps both labels mounted so the row never resizes when the phase flips', () => {
    const html = markup({ kind: 'retrieval', progress: 0.4 });
    expect(html).toContain('Searching for relevant information');
    expect(html).toContain('Generating response');
  });

  it('shows only the current label and hides the other from view', () => {
    const html = markup({ kind: 'generating', progress: 0.8 });
    expect(html.match(/data-active="true"/g)).toHaveLength(1);
    expect(html).toContain('visibility:hidden');
  });

  it('draws the trail at the reported progress', () => {
    expect(markup({ kind: 'retrieval', progress: 0.4 })).toContain('scaleX(0.4)');
  });

  it('never draws a trail so short the head disappears', () => {
    expect(markup({ kind: 'retrieval', progress: 0 })).toContain('scaleX(0.08)');
  });

  it('clamps progress above one so the head cannot leave the track', () => {
    expect(markup({ kind: 'generating', progress: 4 })).toContain('scaleX(1)');
  });

  it('places the head at the leading edge of the trail', () => {
    const html = markup({ kind: 'retrieval', progress: 0.4 });
    expect(html).toContain('translateX(-60%)');
  });
});