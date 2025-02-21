import { defineConfig, loadEnv } from 'vite';
import { resolve } from 'path';

export default defineConfig(({ command, mode }) => {
    // Load env file based on mode
    const env = loadEnv(mode, process.cwd(), '');
    
    return {
        root: '.',
        publicDir: './',
        server: {
            port: 5173,
            proxy: {
                '/vnc': {
                    target: 'http://34.174.193.245:6080',
                    ws: true,
                    secure: false,
                    changeOrigin: true,
                    rewrite: (path) => path.replace(/^\/vnc/, ''),
                    configure: (proxy, options) => {
                        proxy.on('proxyReq', (proxyReq, req, res) => {
                            // Log request details in development
                            if (mode === 'development') {
                                console.log('VNC Proxy Request:', {
                                    url: req.url,
                                    headers: req.headers
                                });
                            }
                        });

                        proxy.on('proxyRes', (proxyRes, req, res) => {
                            // Add CORS headers
                            proxyRes.headers['access-control-allow-origin'] = '*';
                            proxyRes.headers['access-control-allow-methods'] = 'GET,HEAD,PUT,PATCH,POST,DELETE';
                            proxyRes.headers['access-control-allow-headers'] = 'Content-Type, X-Requested-With';

                            // Log response details in development
                            if (mode === 'development') {
                                console.log('VNC Proxy Response:', {
                                    status: proxyRes.statusCode,
                                    headers: proxyRes.headers
                                });
                            }
                        });

                        // Handle WebSocket upgrade
                        proxy.on('upgrade', (req, socket, head) => {
                            if (mode === 'development') {
                                console.log('WebSocket Upgrade Request:', {
                                    url: req.url,
                                    headers: req.headers
                                });
                            }
                        });
                    }
                }
            },
            cors: true
        },
        build: {
            outDir: 'dist',
            rollupOptions: {
                input: {
                    main: resolve(__dirname, 'index.html')
                }
            }
        }
    };
}); 