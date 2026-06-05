import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		host: true,
		strictPort: true,
		hmr: {
			protocol: 'wss',
			host: 'localhost',
			clientPort: 443
		},
		allowedHosts: ['vite']
	}
});
