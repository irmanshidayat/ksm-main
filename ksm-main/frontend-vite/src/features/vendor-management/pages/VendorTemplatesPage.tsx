/**
 * Vendor Templates Page
 * Halaman untuk download template dokumen vendor dengan Tailwind CSS
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetVendorTemplatesQuery } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { ENV } from '@/core/config/env';
import { Button } from '@/shared/components/ui';

const VendorTemplatesPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const { data: templatesData, isLoading, error, refetch } = useGetVendorTemplatesQuery();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [downloading, setDownloading] = useState<number | null>(null);

  // SweetAlert loading
  useEffect(() => {
    if (isLoading) {
      sweetAlert.showLoading('Memuat...', 'Mengambil data template');
    } else {
      sweetAlert.hideLoading();
    }
  }, [isLoading, sweetAlert]);

  // Handle error
  useEffect(() => {
    (async () => {
      if (error && 'status' in error) {
        if (error.status === 401) {
          localStorage.removeItem('KSM_access_token');
          localStorage.removeItem('KSM_refresh_token');
          localStorage.removeItem('KSM_user');
          navigate('/login');
        } else if (error.status !== 404) {
          await sweetAlert.showError('Gagal Memuat', 'Terjadi kesalahan saat memuat template.');
        }
      }
    })();
  }, [error, sweetAlert, navigate]);

  const handleDownload = async (templateId: number, templateName: string) => {
    try {
      setDownloading(templateId);
      const token = localStorage.getItem('KSM_access_token');
      
      sweetAlert.showLoading('Mengunduh...', `Sedang mengunduh ${templateName}`);

      const response = await fetch(`${ENV.API_URL}/api/vendor/templates/${templateId}/download`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      });

      sweetAlert.hideLoading();

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = templateName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        await sweetAlert.showSuccessAuto('Berhasil', 'Template berhasil diunduh');
      } else {
        await sweetAlert.showError('Gagal', 'Gagal mengunduh template');
      }
    } catch (error) {
      sweetAlert.hideLoading();
      await sweetAlert.showError('Kesalahan', 'Terjadi kesalahan saat mengunduh template');
    } finally {
      setDownloading(null);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  if (isLoading) return null;

  if (error && 'status' in error && error.status !== 404) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error</h3>
          <p className="text-red-600 mb-4">Gagal memuat template</p>
          <Button variant="primary" onClick={() => refetch()}>
            Coba Lagi
          </Button>
        </div>
      </div>
    );
  }

  const templates = templatesData?.templates || [];
  const categories = templatesData?.categories || [];

  const filteredTemplates = selectedCategory === 'all'
    ? templates
    : templates.filter((t: any) => t.category === selectedCategory);

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Download Template</h1>
            <p className="text-gray-600">Download template dokumen yang diperlukan untuk penawaran</p>
          </div>
        </div>
      </div>

      {/* Category Filter */}
      {categories.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedCategory('all')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedCategory === 'all'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Semua ({templates.length})
            </button>
            {categories.map((category: any) => (
              <button
                key={category.name}
                onClick={() => setSelectedCategory(category.name)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedCategory === category.name
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {category.display_name || category.name} ({category.count})
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Templates Grid */}
      {filteredTemplates.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map((template: any) => (
            <div
              key={template.id}
              className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">{template.name}</h3>
                  <p className="text-sm text-gray-600 mb-3">{template.description || '-'}</p>
                  <div className="flex flex-wrap gap-2 mb-3">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      {template.category}
                    </span>
                    <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                      {template.file_type}
                    </span>
                    {template.file_size && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                        {formatFileSize(template.file_size)}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <div className="text-xs text-gray-500">
                  {template.download_count || 0} kali diunduh
                </div>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleDownload(template.id, template.name)}
                  disabled={downloading === template.id || !template.file_exists}
                  isLoading={downloading === template.id}
                >
                  {template.file_exists ? '📥 Download' : '❌ Tidak Tersedia'}
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <div className="text-6xl mb-4">📄</div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Tidak Ada Template</h3>
          <p className="text-gray-600">
            {selectedCategory === 'all'
              ? 'Tidak ada template yang tersedia'
              : 'Tidak ada template dalam kategori ini'}
          </p>
        </div>
      )}
    </div>
  );
};

export default VendorTemplatesPage;

