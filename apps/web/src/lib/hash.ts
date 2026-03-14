export async function hashItems(items: string[]): Promise<string> {
  const sorted = [...items].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
  const input = sorted.join('|');
  const encoded = new TextEncoder().encode(input);
  const hashBuffer = await crypto.subtle.digest('SHA-256', encoded);
  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}
