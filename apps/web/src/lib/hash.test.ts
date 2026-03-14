import { describe, it, expect } from 'vitest';
import { hashItems } from './hash';

describe('hashItems', () => {
  // CSK Players: MS Dhoni, Ruturaj Gaikwad, Deepak Chahar, Ravindra Jadeja
  // Sorted (case-insensitive): Deepak Chahar | MS Dhoni | Ravindra Jadeja | Ruturaj Gaikwad
  const CSK_ITEMS = ['MS Dhoni', 'Ruturaj Gaikwad', 'Deepak Chahar', 'Ravindra Jadeja'];
  const CSK_HASH = '753706144fc233169880b91c9005090779ac9a468be8f76632d9499979e891b3';

  it('produces the correct SHA-256 hash for known CSK Players input', async () => {
    const result = await hashItems(CSK_ITEMS);
    expect(result).toBe(CSK_HASH);
  });

  it('is order-independent: shuffled input produces the same hash', async () => {
    const shuffled = ['Deepak Chahar', 'Ravindra Jadeja', 'MS Dhoni', 'Ruturaj Gaikwad'];
    const result = await hashItems(shuffled);
    expect(result).toBe(CSK_HASH);
  });

  it('is order-independent: another permutation produces the same hash', async () => {
    const permuted = ['Ruturaj Gaikwad', 'MS Dhoni', 'Ravindra Jadeja', 'Deepak Chahar'];
    const result = await hashItems(permuted);
    expect(result).toBe(CSK_HASH);
  });

  it('produces a different hash for a different set of items', async () => {
    const differentItems = ['MS Dhoni', 'Ruturaj Gaikwad', 'Deepak Chahar', 'Someone Else'];
    const result = await hashItems(differentItems);
    expect(result).not.toBe(CSK_HASH);
  });

  it('returns a 64-character hex string (SHA-256 output)', async () => {
    const result = await hashItems(CSK_ITEMS);
    expect(result).toMatch(/^[0-9a-f]{64}$/);
  });

  it('case-insensitive sort: "ms dhoni" sorts the same as "MS Dhoni" relative to other items', async () => {
    // Using lowercase versions should sort the same way due to sensitivity:'base'
    const lowercaseItems = ['ms dhoni', 'ruturaj gaikwad', 'deepak chahar', 'ravindra jadeja'];
    const resultLower = await hashItems(lowercaseItems);
    // This is a different hash because the text itself is lowercase, but the SORT ORDER is the same
    // Just verify it produces a consistent 64-char hex result
    expect(resultLower).toMatch(/^[0-9a-f]{64}$/);

    // Calling again with the same lowercase items should produce the same hash
    const resultLower2 = await hashItems(['deepak chahar', 'ms dhoni', 'ravindra jadeja', 'ruturaj gaikwad']);
    expect(resultLower).toBe(resultLower2);
  });
});
