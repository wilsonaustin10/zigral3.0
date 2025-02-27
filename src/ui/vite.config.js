import { defineConfig } from 'vite';
import { resolve } from 'path';
import fs from 'fs';

// Get environment variables
const vncHost = process.env.VNC_HOST || 'localhost';
const vncPort = process.env.VNC_PORT || '6080';

// Create a small HTML file to redirect to the frontend
const createRedirectHtml = () => {
  const redirectHtml = `
<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="refresh" content="0;URL='/ui/'" />
  <title>Redirecting to Zigral UI</title>
</head>
<body>
  <p>Redirecting to <a href="/ui/">Zigral UI</a>...</p>
</body>
</html>
`;
  
  // Make sure the public directory exists
  if (!fs.existsSync('./public')) {
    fs.mkdirSync('./public', { recursive: true });
  }
  
  // Write the redirect file
  fs.writeFileSync('./public/index.html', redirectHtml);
};

// Create the redirect file
createRedirectHtml();

// Copy the test-novnc.html to make it directly accessible at /test-novnc.html
if (fs.existsSync('./public/test-novnc.html')) {
  fs.copyFileSync('./public/test-novnc.html', './test-novnc.html');
}

export default defineConfig({
  root: './',
  base: '/ui/',
  publicDir: 'public',
  assetsInclude: ['**/*.js'], // Ensure JS files are treated as assets
  server: {
    host: '0.0.0.0',
    port: 8090,
    strictPort: true,
    // Proxy the WebSocket connections to the VNC server
    proxy: {
      '/websockify': {
        target: `ws://${vncHost}:${vncPort}`,
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/websockify/, '/websockify'),
      }
    },
    fs: {
      // Allow serving files from one level up
      allow: ['.', '..', '../../', 'public'],
      // Explicitly allow access to the novnc directory
      strict: false
    },
    cors: {
      origin: '*'
    },
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Content-Security-Policy': "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline' 'unsafe-eval'; connect-src 'self' ws: wss:; img-src 'self' data:; style-src 'self' 'unsafe-inline';"
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
      },
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './'),
    },
  },
  // Configure environment variables to be passed to the frontend
  define: {
    'process.env.VNC_HOST': JSON.stringify(vncHost),
    'process.env.VNC_PORT': JSON.stringify(vncPort),
  },
}); 