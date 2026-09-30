import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
const apiTarget=process.env.SKYGUARD_API_TARGET||'http://127.0.0.1:8010';
export default defineConfig({plugins:[react()],server:{port:5173,proxy:{'/api':apiTarget,'/docs':apiTarget,'/openapi.json':apiTarget,'/ws':{target:apiTarget.replace(/^http/,'ws'),ws:true}}}});
