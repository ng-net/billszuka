import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const rootMaster = path.resolve(__dirname, '../../data/master.csv');
const targetMaster = path.resolve(__dirname, '../public/master.csv');
const targetSample = path.resolve(__dirname, '../public/sample.csv');

try {
  if (fs.existsSync(rootMaster)) {
    const data = fs.readFileSync(rootMaster);
    fs.writeFileSync(targetMaster, data);
    fs.writeFileSync(targetSample, data);
    console.log(`[sync-data] Synchronized master.csv (${data.length} bytes) to public/`);
  } else {
    console.log('[sync-data] root data/master.csv not found, keeping existing public/master.csv');
  }
} catch (err) {
  console.warn('[sync-data] Warning syncing data:', err.message);
}
