/**
 * Login Page
 * Authentication login page dengan Tailwind CSS
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useSweetAlert } from '@/shared/hooks/useSweetAlert';
import { Input, Button, LoadingSpinner } from '@/shared/components/ui';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login, user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();

  // Auto-redirect jika sudah login
  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.role === 'vendor') {
        navigate('/vendor/dashboard');
      } else {
        navigate('/dashboard');
      }
    }
  }, [isAuthenticated, user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const success = await login(username, password);
      if (success) {
        const userInfo = localStorage.getItem('KSM_user');
        if (userInfo) {
          try {
            const user = JSON.parse(userInfo);
            await sweetAlert.showSuccessAuto('Login Berhasil', 'Selamat datang! Anda akan diarahkan ke dashboard.');
            if (user.role === 'vendor') {
              navigate('/vendor/dashboard');
            } else {
              navigate('/dashboard');
            }
          } catch (error) {
            navigate('/dashboard');
          }
        } else {
          navigate('/dashboard');
        }
      } else {
        await sweetAlert.showError('Login Gagal', 'Username atau password salah. Silakan coba lagi.');
      }
    } catch (err) {
      await sweetAlert.showError('Kesalahan', 'Terjadi kesalahan saat login. Silakan coba lagi.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-bg-secondary">
      <div className="max-w-md w-full bg-bg-primary rounded-lg shadow-lg p-8 mobile:p-4">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-text-primary mb-2">KSM Main</h1>
          <p className="text-text-secondary">Silakan login untuk melanjutkan</p>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-6">
          <p className="text-sm text-green-800">
            <strong>Info:</strong> Halaman login untuk semua user (Admin, Staff, dan Vendor). 
            Sistem akan otomatis mengarahkan ke dashboard yang sesuai.
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Username"
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={loading}
            autoComplete="username"
          />
          
          <Input
            label="Password"
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
            autoComplete="current-password"
          />
          
          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full"
            isLoading={loading}
            disabled={loading}
          >
            {loading ? 'Memproses...' : 'Login'}
          </Button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;

