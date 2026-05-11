import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
    plugins: [sveltekit()],
    server: {
        // This is the magic block!
        proxy: {
            // 1. Forward all API requests to FastAPI
            '/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
                secure: false, // Ignore SSL certificate errors from localhost
            },
            // 2. Forward all WebSocket requests to FastAPI
            '/ws': {
                target: 'http://127.0.0.1:8000',
                ws: true, // Tell Vite this is a WebSocket
                changeOrigin: true,
                secure: false,
            }
        }
    }
});