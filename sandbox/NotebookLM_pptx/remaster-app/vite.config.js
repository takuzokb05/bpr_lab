import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import topLevelAwait from "vite-plugin-top-level-await";
import wasm from "vite-plugin-wasm";
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        react(),
        wasm(),
        topLevelAwait()
    ],

    build: {
        target: 'esnext'
    },
    optimizeDeps: {
        esbuildOptions: {
            target: 'esnext'
        }
    }
})
