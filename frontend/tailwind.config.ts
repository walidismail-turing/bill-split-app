import type { Config } from 'tailwindcss';

export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			fontFamily: {
				sans: ['ui-sans-serif', 'system-ui', 'Inter', 'Segoe UI', 'Roboto', 'Arial', 'sans-serif']
			},
			boxShadow: {
				soft: '0 10px 30px rgba(0,0,0,0.12)'
			}
		}
	},
	plugins: []
} satisfies Config;

