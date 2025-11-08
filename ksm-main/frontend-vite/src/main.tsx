/**
 * Main Entry Point
 * Application entry point dengan React 18 createRoot
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import ErrorBoundary from './shared/components/ErrorBoundary';
import './styles/globals.css';

// Ensure viewport meta for responsive behavior on mobile devices
(() => {
  if (typeof document !== 'undefined' && !document.querySelector('meta[name="viewport"]')) {
    const meta = document.createElement('meta');
    meta.name = 'viewport';
    meta.content = 'width=device-width, initial-scale=1, maximum-scale=1';
    document.head.appendChild(meta);
  }
})();

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Root element not found');
}

try {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </React.StrictMode>
  );
} catch (error) {
  console.error('Failed to render app:', error);
  rootElement.innerHTML = `
    <div style="display: flex; align-items: center; justify-content: center; min-height: 100vh; background: #f3f4f6; flex-direction: column; padding: 2rem;">
      <h1 style="color: #dc2626; font-size: 2rem; margin-bottom: 1rem;">⚠️ Error Loading App</h1>
      <p style="color: #6b7280; margin-bottom: 1rem;">${error instanceof Error ? error.message : 'Unknown error'}</p>
      <button onclick="window.location.reload()" style="padding: 0.5rem 1rem; background: #2563eb; color: white; border: none; border-radius: 0.5rem; cursor: pointer;">
        Refresh Page
      </button>
    </div>
  `;
}

