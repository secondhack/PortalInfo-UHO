import React from 'react';
import {createRoot} from 'react-dom/client';
import {AuthProvider} from './contexts/Auth';
import App from './routes/App';
import './styles/global.css';
createRoot(document.getElementById('root')).render(<AuthProvider><App/></AuthProvider>);
