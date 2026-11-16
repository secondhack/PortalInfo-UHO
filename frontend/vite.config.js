import { defineConfig } from 'vite';
const target=process.env.API_PROXY_TARGET || 'http://127.0.0.1:8010';
export default defineConfig({server:{proxy:{'/api':target,'/auth':target}},build:{rollupOptions:{output:{manualChunks(id){if(id.includes('node_modules/chart.js')||id.includes('@kurkle/color'))return 'charts';}}}},test:{include:['src/**/*.test.{js,jsx}'],environment:'jsdom',setupFiles:['./src/test-setup.js']}});
