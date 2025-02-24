import { defineConfig, loadEnv } from 'vite';
import { resolve } from 'path';

export default defineConfig(({ command, mode }) => {
    // Load env file based on mode
    const env = loadEnv(mode, process.cwd(), '');
    
    return {
        root: '.',
        publicDir: './',
        define: {
            __DEFINES__: {},
            'process.env': env
        },
        server: {
            port: 5173,
            proxy: {
                '/vnc': {
                    target: 'http://34.174.193.245:6081',
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

                        // Log any proxy errors
                        proxy.on('error', (err, req, res) => {
                            if (mode === 'development') {
                                console.error('VNC Proxy encountered an error:', err);
                                if (err && err.code === 'ECONNREFUSED') {
                                    console.error('ECONNREFUSED error detected. Websockify may be down. Scheduling retry in 2000ms.');
                                    setTimeout(() => {
                                        console.log('Retrying proxy connection attempt after ECONNREFUSED error.');
                                        // TODO: Optionally trigger additional logic or alerting here
                                    }, 2000);
                                }
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