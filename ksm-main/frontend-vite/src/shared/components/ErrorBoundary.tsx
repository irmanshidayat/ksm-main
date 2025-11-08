/**
 * Error Boundary Component
 * Catch error dan tampilkan fallback UI
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
          <div className="text-center p-8">
            <h1 className="text-3xl font-bold text-red-600 mb-4">⚠️ Terjadi Kesalahan</h1>
            <p className="text-gray-600 mb-4">
              {this.state.error?.message || 'Terjadi kesalahan saat memuat aplikasi'}
            </p>
            <div className="space-x-4">
              <button
                onClick={() => window.location.reload()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Refresh Halaman
              </button>
              <button
                onClick={() => this.setState({ hasError: false, error: null })}
                className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Coba Lagi
              </button>
            </div>
            {this.state.error && (
              <details className="mt-6 text-left bg-gray-200 p-4 rounded max-w-2xl mx-auto">
                <summary className="cursor-pointer font-semibold text-gray-800">
                  Detail Error
                </summary>
                <pre className="mt-2 text-xs text-gray-700 overflow-auto">
                  {this.state.error.stack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

