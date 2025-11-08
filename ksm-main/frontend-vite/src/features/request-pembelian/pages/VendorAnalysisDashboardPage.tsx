/**
 * Vendor Analysis Dashboard Page
 * Halaman analisis vendor untuk request pembelian dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useGetRequestPembelianByIdQuery, useGetVendorAnalysisQuery, useGetVendorPenawaransQuery } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';

const VendorAnalysisDashboardPage: React.FC = () => {
  const { requestId } = useParams<{ requestId: string }>();
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const reqId = requestId ? parseInt(requestId) : 0;

  const { data: request, isLoading: loadingRequest } = useGetRequestPembelianByIdQuery(reqId, { skip: !reqId });
  const { data: analysisResult, isLoading: loadingAnalysis, refetch: refetchAnalysis } = useGetVendorAnalysisQuery(reqId, { skip: !reqId });
  const { data: penawarans = [] } = useGetVendorPenawaransQuery(reqId, { skip: !reqId });

  // Transform analysis data
  const analysisData = analysisResult ? (Array.isArray(analysisResult) ? analysisResult : [analysisResult]) : [];

  const [sortBy, setSortBy] = useState<'total_score' | 'price' | 'delivery'>('total_score');

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    if (score >= 40) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  };

  const getRecommendationColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'strongly_recommend': return 'bg-green-100 text-green-800';
      case 'recommend': return 'bg-blue-100 text-blue-800';
      case 'consider': return 'bg-yellow-100 text-yellow-800';
      case 'not_recommend': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getRecommendationText = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'strongly_recommend': return 'Sangat Direkomendasikan';
      case 'recommend': return 'Direkomendasikan';
      case 'consider': return 'Pertimbangkan';
      case 'not_recommend': return 'Tidak Direkomendasikan';
      default: return 'Pertimbangkan';
    }
  };

  if (loadingRequest || loadingAnalysis) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (!request) {
    return (
      <div className="p-4 md:p-6 lg:p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">Request Tidak Ditemukan</h3>
          <Button variant="primary" onClick={() => navigate('/request-pembelian/daftar-request')}>
            Kembali
          </Button>
        </div>
      </div>
    );
  }

  const analysisResults = analysisData || [];

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">Analisis Vendor</h1>
            <p className="text-gray-600">Request: {request.title} ({request.reference_id})</p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => refetchAnalysis()}
            >
              🔄 Refresh
            </Button>
            <Link to={`/request-pembelian/detail/${request.id}`}>
              <Button variant="outline">
                ← Kembali
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">🏢</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{penawarans.length}</h3>
              <p className="text-sm text-gray-600">Total Penawaran</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📊</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">{analysisResults.length}</h3>
              <p className="text-sm text-gray-600">Vendor Dianalisis</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">💰</div>
            <div>
              <h3 className="text-2xl font-bold text-gray-800">
                {formatCurrency(request.total_budget || 0)}
              </h3>
              <p className="text-sm text-gray-600">Total Budget</p>
            </div>
          </div>
        </div>
      </div>

      {/* Sort & Filter */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="total_score">Total Score</option>
              <option value="price">Price</option>
              <option value="delivery">Delivery Time</option>
            </select>
          </div>
        </div>
      </div>

      {/* Analysis Results */}
      {analysisResults.length > 0 ? (
        <div className="space-y-4">
          {analysisResults.map((result: any, index: number) => (
            <div key={index} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">
                    {result.vendor?.company_name || 'Vendor'}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {result.vendor?.email || '-'} | {result.vendor?.vendor_category || '-'}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRecommendationColor(result.analysis?.recommendation_level || '')}`}>
                    {getRecommendationText(result.analysis?.recommendation_level || '')}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(result.analysis?.total_score || 0)}`}>
                    Score: {result.analysis?.total_score?.toFixed(1) || 0}%
                  </span>
                </div>
              </div>

              {/* Score Breakdown */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Price Score</label>
                  <p className="text-sm font-medium">{result.analysis?.price_score?.toFixed(1) || 0}%</p>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Quality Score</label>
                  <p className="text-sm font-medium">{result.analysis?.quality_score?.toFixed(1) || 0}%</p>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Delivery Score</label>
                  <p className="text-sm font-medium">{result.analysis?.delivery_score?.toFixed(1) || 0}%</p>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Reputation Score</label>
                  <p className="text-sm font-medium">{result.analysis?.reputation_score?.toFixed(1) || 0}%</p>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Payment Score</label>
                  <p className="text-sm font-medium">{result.analysis?.payment_score?.toFixed(1) || 0}%</p>
                </div>
              </div>

              {/* Penawaran Info */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Total Price</label>
                  <p className="text-sm font-medium">{formatCurrency(result.penawaran?.total_quoted_price || 0)}</p>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Delivery Time</label>
                  <p className="text-sm font-medium">{result.penawaran?.delivery_time_days || 0} days</p>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Payment Terms</label>
                  <p className="text-sm font-medium">{result.penawaran?.payment_terms || '-'}</p>
                </div>
              </div>

              {result.analysis?.analysis_date && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-500">
                    Analisis: {formatDate(result.analysis.analysis_date)} | Method: {result.analysis.analysis_method || 'N/A'}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <div className="text-6xl mb-4">📊</div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Belum Ada Analisis</h3>
          <p className="text-gray-600 mb-4">
            {penawarans.length > 0 
              ? 'Belum ada hasil analisis untuk penawaran ini'
              : 'Belum ada penawaran untuk request ini'}
          </p>
          {penawarans.length === 0 && (
            <Link to={`/request-pembelian/upload-penawaran`}>
              <Button variant="primary">
                Upload Penawaran
              </Button>
            </Link>
          )}
        </div>
      )}
    </div>
  );
};

export default VendorAnalysisDashboardPage;

