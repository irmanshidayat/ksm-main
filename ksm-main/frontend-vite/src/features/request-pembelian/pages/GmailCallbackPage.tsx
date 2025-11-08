/**
 * Gmail Callback Page
 * Halaman untuk handle OAuth callback dari Gmail dengan Tailwind CSS
 */

import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useSweetAlert } from '@/shared/hooks';
import { Button, LoadingSpinner } from '@/shared/components/ui';

const GmailCallbackPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Memproses koneksi Gmail...');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const errorParam = searchParams.get('error');

        if (errorParam) {
          setStatus('error');
          setMessage('Gagal menghubungkan Gmail');
          setError(`Error: ${errorParam}`);
          return;
        }

        if (!code || !state) {
          setStatus('error');
          setMessage('Parameter callback tidak valid');
          setError('Code atau state tidak ditemukan');
          return;
        }

        setMessage('Menyelesaikan koneksi Gmail...');
        
        // Call API untuk handle callback
        const response = await fetch('/api/gmail/auth/callback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ code, state }),
        });

        const result = await response.json();
        
        if (result.success) {
          setStatus('success');
          setMessage('Gmail berhasil terhubung!');
          
          // Redirect ke EmailComposer setelah 2 detik
          setTimeout(() => {
            navigate('/request-pembelian/email-composer');
          }, 2000);
        } else {
          setStatus('error');
          setMessage('Gagal menghubungkan Gmail');
          setError(result.message || 'Gagal menghubungkan Gmail');
        }
      } catch (err: any) {
        console.error('Gmail callback error:', err);
        setStatus('error');
        setMessage('Terjadi kesalahan saat menghubungkan Gmail');
        setError(err?.message || 'Terjadi kesalahan yang tidak terduga');
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  const handleRetry = () => {
    navigate('/request-pembelian/email-composer');
  };

  const handleClose = () => {
    navigate('/request-pembelian/email-composer');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-md p-8 max-w-md w-full">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">🔗 Gmail Integration</h2>
        </div>

        <div className="text-center">
          {status === 'processing' && (
            <div className="space-y-4">
              <LoadingSpinner />
              <p className="text-gray-600">{message}</p>
            </div>
          )}

          {status === 'success' && (
            <div className="space-y-4">
              <div className="text-6xl mb-4">✅</div>
              <h3 className="text-xl font-semibold text-gray-800">Berhasil!</h3>
              <p className="text-gray-600">{message}</p>
              <p className="text-sm text-gray-500 mt-2">
                Mengalihkan ke halaman Email Composer...
              </p>
            </div>
          )}

          {status === 'error' && (
            <div className="space-y-4">
              <div className="text-6xl mb-4">❌</div>
              <h3 className="text-xl font-semibold text-gray-800">Gagal</h3>
              <p className="text-gray-600">{message}</p>
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mt-4">
                  <p className="text-sm font-semibold text-red-800 mb-1">Detail Error:</p>
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}
              <div className="flex gap-2 justify-center mt-6">
                <Button variant="primary" onClick={handleRetry}>
                  🔄 Coba Lagi
                </Button>
                <Button variant="outline" onClick={handleClose}>
                  ❌ Tutup
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GmailCallbackPage;

