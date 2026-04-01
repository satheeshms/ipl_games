import { readdirSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const canonicalUrl = process.env.VITE_CANONICAL_URL;
if (!canonicalUrl) {
  console.error('Error: VITE_CANONICAL_URL environment variable is not set.');
  console.error('Set it before running the build, e.g.:');
  console.error('  VITE_CANONICAL_URL=https://cluster4.games npm run build');
  process.exit(1);
}

const puzzleDir = join(__dirname, '..', 'public', 'puzzles', 'ipl');
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const todayUtc = new Date().toISOString().slice(0, 10);

let files;
try {
  files = readdirSync(puzzleDir);
} catch {
  console.error(`Error: could not read puzzle directory: ${puzzleDir}`);
  process.exit(1);
}

const dates = files
  .filter(f => f.endsWith('.json') && DATE_RE.test(f.replace('.json', '')))
  .map(f => f.replace('.json', ''))
  .sort();

const urlEntries = dates.map(date => `  <url>
    <loc>${canonicalUrl}/</loc>
    <lastmod>${date}</lastmod>
    <changefreq>yearly</changefreq>
    <priority>${date === todayUtc ? '0.8' : '0.5'}</priority>
  </url>`).join('\n');

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urlEntries}
</urlset>
`;

const robotsTxt = `User-agent: *
Disallow:

Sitemap: ${canonicalUrl}/sitemap.xml
`;

writeFileSync(join(__dirname, '..', 'public', 'sitemap.xml'), sitemap);
writeFileSync(join(__dirname, '..', 'public', 'robots.txt'), robotsTxt);

console.log(`Generated sitemap.xml with ${dates.length} entries. robots.txt updated.`);
