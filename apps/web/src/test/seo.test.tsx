import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { HelmetProvider } from 'react-helmet-async';
import { GameSEO } from '../components/GameSEO';
import type { Puzzle } from '../types';

const MOCK_PUZZLE: Puzzle = {
  id: 'test',
  date: '2026-04-01',
  edition: 42,
  items: [
    'MS Dhoni', 'Rohit Sharma', 'Virat Kohli', 'KL Rahul',
    'Jasprit Bumrah', 'Ravindra Jadeja', 'Hardik Pandya', 'Yuzvendra Chahal',
    'Rishabh Pant', 'Shubman Gill', 'Faf du Plessis', 'David Warner',
    'AB de Villiers', 'Chris Gayle', 'Kieron Pollard', 'Andre Russell',
  ],
  categories: [
    { color: 'yellow', title: 'CSK Players', hash: 'abc' },
    { color: 'green',  title: 'MI Players',  hash: 'def' },
    { color: 'blue',   title: 'RCB Players', hash: 'ghi' },
    { color: 'purple', title: 'KKR Players', hash: 'jkl' },
  ],
};

function renderGameSEO() {
  return render(
    <HelmetProvider>
      <GameSEO puzzle={MOCK_PUZZLE} />
    </HelmetProvider>,
  );
}

describe('GameSEO', () => {
  it('sets the document title with edition and date', () => {
    renderGameSEO();
    expect(document.title).toBe('Puzzle #42 – 2026-04-01 | Cluster 4 - IPL Edition');
  });

  it('sets a canonical link tag', () => {
    renderGameSEO();
    const canonical = document.querySelector('link[rel="canonical"]');
    expect(canonical).not.toBeNull();
  });

  it('sets og:title meta tag with edition and date', () => {
    renderGameSEO();
    const ogTitle = document.querySelector('meta[property="og:title"]');
    expect(ogTitle?.getAttribute('content')).toBe('Puzzle #42 – 2026-04-01');
  });

  it('sets og:description meta tag mentioning edition', () => {
    renderGameSEO();
    const ogDesc = document.querySelector('meta[property="og:description"]');
    expect(ogDesc?.getAttribute('content')).toContain('#42');
  });

  it('sets description meta tag mentioning edition', () => {
    renderGameSEO();
    const desc = document.querySelector('meta[name="description"]');
    expect(desc?.getAttribute('content')).toContain('#42');
    expect(desc?.getAttribute('content')).toContain('2026-04-01');
  });

  it('does not leak category hashes or titles into the document head', () => {
    renderGameSEO();
    const headHtml = document.head.innerHTML;
    expect(headHtml).not.toContain('abc');
    expect(headHtml).not.toContain('CSK Players');
  });
});
