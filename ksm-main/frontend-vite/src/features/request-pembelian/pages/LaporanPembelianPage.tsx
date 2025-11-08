/**
 * Laporan Pembelian Page
 * Coming Soon page untuk fitur laporan pembelian dengan Tailwind CSS
 */

import React from 'react';

const LaporanPembelianPage: React.FC = () => {
  return (
    <div className="p-4 md:p-6 lg:p-8">
      <div className="bg-white rounded-lg shadow-md p-8 md:p-12 text-center">
        <div className="max-w-2xl mx-auto">
          <div className="text-6xl mb-6">🚧</div>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-800 mb-4">📊 Laporan Pembelian</h1>
          <p className="text-lg text-gray-600 mb-8">
            Fitur laporan pembelian sedang dalam pengembangan
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-blue-900 mb-2">Fitur yang Akan Tersedia:</h2>
            <ul className="text-left text-blue-800 space-y-2 max-w-md mx-auto">
              <li>• Laporan pembelian per periode</li>
              <li>• Analisis pengeluaran</li>
              <li>• Statistik vendor</li>
              <li>• Export laporan ke Excel/PDF</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LaporanPembelianPage;

