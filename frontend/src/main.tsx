import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';

// Apply saved theme before first render to prevent flash
const savedTheme = localStorage.getItem('moa:theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);

createRoot(document.getElementById('root')!).render(<App />);
