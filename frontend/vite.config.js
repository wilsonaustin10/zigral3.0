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
                    target: `${env.VNC_HOST}:${env.VNC_PORT}`,
                    ws: true,
                    secure: false,
                    changeOrigin: true,
                    rewrite: (path) => path.replace(/^\/vnc/, ''),
                },
                '/kasm-proxy': {
                    target: env.VITE_KASM_HOST || 'https://34.136.51.93:443',
                    changeOrigin: true,
                    secure: false,
                    rewrite: (path) => path.replace(/^\/kasm-proxy/, ''),
                    configure: (proxy, options) => {
                        proxy.on('proxyReq', (proxyReq, req, res) => {
                            // Log request details in development
                            if (mode === 'development') {
                                console.log('Proxying request:', {
                                    url: req.url,
                                    headers: req.headers,
                                    cookies: req.headers.cookie
                                });
                            }

                            // Preserve cookies
                            if (req.headers.cookie) {
                                proxyReq.setHeader('Cookie', req.headers.cookie);
                            }

                            // Set origin header to match target
                            proxyReq.setHeader('Origin', env.VITE_KASM_HOST || 'https://34.136.51.93:443');
                        });

                        proxy.on('proxyRes', (proxyRes, req, res) => {
                            // Add CORS and cookie headers
                            proxyRes.headers['access-control-allow-origin'] = 'http://localhost:5173';
                            proxyRes.headers['access-control-allow-credentials'] = 'true';
                            proxyRes.headers['access-control-allow-methods'] = 'GET,HEAD,PUT,PATCH,POST,DELETE';
                            proxyRes.headers['access-control-allow-headers'] = 'Content-Type, Authorization, X-Requested-With';

                            // Log response details in development
                            if (mode === 'development') {
                                console.log('Proxy response:', {
                                    status: proxyRes.statusCode,
                                    headers: proxyRes.headers,
                                    cookies: proxyRes.headers['set-cookie']
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