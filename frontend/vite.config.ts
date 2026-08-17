import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		host: true,
		strictPort: true,
		hmr: {
			protocol: 'wss',
			host: 'localhost',
			clientPort: 8443
		},
		allowedHosts: ['vite']
	}
});
