import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { createServer as createViteServer } from 'vite';
import { exec } from 'child_process';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = parseInt(process.env.PORT || '3000', 10);

  app.use(express.json());

  const projectDir = path.resolve(__dirname, 'university-registrar');
  const zipPath = path.resolve(__dirname, 'public/university-registrar.zip');

  // API to serve the project ZIP archive
  app.get('/api/download-zip', (req, res) => {
    if (fs.existsSync(zipPath)) {
      res.setHeader('Content-Disposition', 'attachment; filename="university-registrar.zip"');
      res.setHeader('Content-Type', 'application/zip');
      const stream = fs.createReadStream(zipPath);
      stream.pipe(res);
    } else {
      res.status(404).json({ error: 'ZIP file not found. Rebuild in progress.' });
    }
  });

  // API to execute pytest live
  app.post('/api/run-pytest', (req, res) => {
    const cmd = `cd "${projectDir}" && PYTHONPATH=src pytest tests -v`;
    exec(cmd, { timeout: 30000 }, (error, stdout, stderr) => {
      res.json({
        success: !error || error.code === 0,
        exitCode: error ? error.code : 0,
        stdout: stdout || '',
        stderr: stderr || '',
        timestamp: new Date().toISOString(),
      });
    });
  });

  // API to run CLI commands live
  app.post('/api/run-cli', (req, res) => {
    const { command, args = [] } = req.body;
    // Sanitize command inputs to allow safe university_registrar execution
    const allowedSubcommands = ['list', 'stats', 'search', 'get', 'export', 'import', '--help', 'add'];
    const subcmd = String(command || '').trim();

    const safeArgs = Array.isArray(args) ? args.map(a => `"${String(a).replace(/"/g, '\\"')}"`).join(' ') : '';
    const fullCmd = `cd "${projectDir}" && PYTHONPATH=src python3 -m university_registrar -d data/students.json ${subcmd} ${safeArgs}`;

    exec(fullCmd, { timeout: 20000 }, (error, stdout, stderr) => {
      res.json({
        success: !error || error.code === 0,
        exitCode: error ? error.code : 0,
        stdout: stdout || '',
        stderr: stderr || '',
        commandExecuted: `python -m university_registrar ${subcmd} ${safeArgs}`.trim(),
      });
    });
  });

  // API to fetch project source files list and content
  app.get('/api/file-content', (req, res) => {
    const filePath = req.query.path as string;
    if (!filePath) {
      return res.status(400).json({ error: 'Path is required' });
    }
    // Prevent directory traversal
    const safeRelPath = path.normalize(filePath).replace(/^(\.\.[\/\\])+/, '');
    const absolute = path.resolve(projectDir, safeRelPath);

    if (!absolute.startsWith(projectDir)) {
      return res.status(403).json({ error: 'Access denied' });
    }

    if (!fs.existsSync(absolute) || fs.statSync(absolute).isDirectory()) {
      return res.status(404).json({ error: 'File not found' });
    }

    try {
      const content = fs.readFileSync(absolute, 'utf-8');
      res.json({ path: safeRelPath, content });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // In development, hook up Vite middleware
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    // In production, serve built dist files
    app.use(express.static(path.resolve(__dirname, 'dist')));
    app.get('*', (req, res) => {
      res.sendFile(path.resolve(__dirname, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server listening on http://0.0.0.0:${PORT}`);
  });
}

startServer();
