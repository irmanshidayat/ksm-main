/**
 * Daftar Barang Masuk Page
 * Halaman untuk melihat daftar semua barang masuk dengan filter, sort, dan pagination
 */

import React, { useState, useMemo } from 'react';
import { useGetBarangMasukListQuery } from '../store/stokBarangApi';
import { LoadingSpinner } from '@/shared/components/feedback';
import { Table } from '@/shared/components/ui';
import type { BarangMasukData } from '../types';

const DaftarBarangMasukPage: React.FC = () => {
  const { data: barangMasukList = [], isLoading, error, refetch } = useGetBarangMasukListQuery();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterKategori, setFilterKategori] = useState<string>('');
  const [sortBy, setSortBy] = useState<'tanggal' | 'nama' | 'jumlah'>('tanggal');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Get unique categories for filter
  const uniqueKategori = useMemo(() => {
    const kategoriList = barangMasukList
      .filter(item => item?.barang?.kategori?.nama_kategori)
      .map(item => item.barang.kategori.nama_kategori);
    return Array.from(new Set(kategoriList));
  }, [barangMasukList]);

  // Filter dan sort data
  const filteredData = useMemo(() => {
    return barangMasukList
      .filter(item => {
        if (!item || !item.barang || !item.barang.nama_barang || !item.barang.kode_barang) {
          return false;
        }
        
        const matchesSearch = 
          item.barang.nama_barang.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.barang.kode_barang.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (item.nomor_surat_jalan && item.nomor_surat_jalan.toLowerCase().includes(searchTerm.toLowerCase()));
        
        const matchesKategori = 
          filterKategori === '' || 
          (item.barang.kategori && item.barang.kategori.nama_kategori === filterKategori);
        
        return matchesSearch && matchesKategori;
      })
      .sort((a, b) => {
        if (!a || !b || !a.barang || !b.barang) return 0;
        
        let comparison = 0;
        switch (sortBy) {
          case 'tanggal':
            comparison = new Date(a.tanggal_masuk || 0).getTime() - new Date(b.tanggal_masuk || 0).getTime();
            break;
          case 'nama':
            comparison = (a.barang.nama_barang || '').localeCompare(b.barang.nama_barang || '');
            break;
          case 'jumlah':
            comparison = (a.jumlah_masuk || 0) - (b.jumlah_masuk || 0);
            break;
        }
        
        return sortOrder === 'asc' ? comparison : -comparison;
      });
  }, [barangMasukList, searchTerm, filterKategori, sortBy, sortOrder]);

  // Pagination
  const totalPages = Math.ceil(filteredData.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentData = filteredData.slice(startIndex, endIndex);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('id-ID', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner message="Memuat data barang masuk..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 md:p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <span className="text-4xl mb-4 block">❌</span>
          <p className="text-red-700 mb-4">Gagal memuat data barang masuk</p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            🔄 Coba Lagi
          </button>
        </div>
      </div>
    );
  }

  const totalNilai = filteredData.reduce(
    (total, item) => total + (item.harga_per_unit || 0) * item.jumlah_masuk,
    0
  );
  const hariIni = filteredData.filter(
    item => new Date(item.tanggal_masuk).toDateString() === new Date().toDateString()
  ).length;

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📋 Daftar Barang Masuk</h1>
        <p className="text-gray-600">Lihat semua barang masuk yang telah ditambahkan ke inventory</p>
      </div>

      {/* Filter dan Search */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <input
              type="text"
              placeholder="🔍 Cari barang, kode, atau nomor surat jalan..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <select
            value={filterKategori}
            onChange={(e) => setFilterKategori(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Semua Kategori</option>
            {uniqueKategori.map(kategori => (
              <option key={kategori} value={kategori}>{kategori}</option>
            ))}
          </select>

          <div className="flex gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'tanggal' | 'nama' | 'jumlah')}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="tanggal">Urutkan: Tanggal</option>
              <option value="nama">Urutkan: Nama</option>
              <option value="jumlah">Urutkan: Jumlah</option>
            </select>

            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </button>
          </div>
        </div>
      </div>

      {/* Statistik */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📦</div>
            <div>
              <h3 className="text-sm text-gray-600 mb-1">Total Barang Masuk</h3>
              <p className="text-2xl font-bold text-gray-800">{filteredData.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">💰</div>
            <div>
              <h3 className="text-sm text-gray-600 mb-1">Total Nilai</h3>
              <p className="text-2xl font-bold text-gray-800">{formatCurrency(totalNilai)}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-4">
            <div className="text-4xl">📅</div>
            <div>
              <h3 className="text-sm text-gray-600 mb-1">Hari Ini</h3>
              <p className="text-2xl font-bold text-gray-800">{hariIni}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabel Barang Masuk */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        {currentData.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-6xl mb-4">📭</div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">Tidak ada data barang masuk</h3>
            <p className="text-gray-600">
              Belum ada barang masuk yang ditambahkan atau data tidak ditemukan dengan filter yang dipilih.
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <Table.Header>
                  <Table.Row>
                    <Table.Head>No</Table.Head>
                    <Table.Head>Tanggal</Table.Head>
                    <Table.Head>Kode Barang</Table.Head>
                    <Table.Head>Nama Barang</Table.Head>
                    <Table.Head>Kategori</Table.Head>
                    <Table.Head>Jumlah</Table.Head>
                    <Table.Head>Harga/Unit</Table.Head>
                    <Table.Head>Total Harga</Table.Head>
                    <Table.Head>Supplier</Table.Head>
                    <Table.Head>No. Surat Jalan</Table.Head>
                    <Table.Head>Keterangan</Table.Head>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {currentData.map((item, index) => (
                    <Table.Row key={item.id}>
                      <Table.Cell>{startIndex + index + 1}</Table.Cell>
                      <Table.Cell>
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                          {formatDate(item.tanggal_masuk)}
                        </span>
                      </Table.Cell>
                      <Table.Cell>
                        <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-sm font-mono">
                          {item.barang.kode_barang}
                        </span>
                      </Table.Cell>
                      <Table.Cell>
                        <strong>{item.barang.nama_barang}</strong>
                      </Table.Cell>
                      <Table.Cell>
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
                          {item.barang.kategori?.nama_kategori || '-'}
                        </span>
                      </Table.Cell>
                      <Table.Cell>
                        <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-sm">
                          {item.jumlah_masuk} {item.barang.satuan}
                        </span>
                      </Table.Cell>
                      <Table.Cell>
                        {item.harga_per_unit ? formatCurrency(item.harga_per_unit) : '-'}
                      </Table.Cell>
                      <Table.Cell>
                        {item.harga_per_unit ? (
                          <span className="font-semibold text-green-700">
                            {formatCurrency(item.harga_per_unit * item.jumlah_masuk)}
                          </span>
                        ) : '-'}
                      </Table.Cell>
                      <Table.Cell>
                        {item.supplier?.nama_supplier || '-'}
                      </Table.Cell>
                      <Table.Cell>
                        {item.nomor_surat_jalan || '-'}
                      </Table.Cell>
                      <Table.Cell>
                        <span className="text-sm text-gray-600">{item.keterangan || '-'}</span>
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="p-4 border-t border-gray-200 flex items-center justify-between">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  ← Sebelumnya
                </button>
                
                <div className="flex gap-2">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`px-4 py-2 rounded-lg transition-colors ${
                        currentPage === page
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {page}
                    </button>
                  ))}
                </div>
                
                <button
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Selanjutnya →
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mt-6 flex gap-4 justify-end">
        <button
          onClick={() => refetch()}
          className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          🔄 Refresh Data
        </button>
        
        <button
          onClick={() => window.print()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          disabled={currentData.length === 0}
        >
          🖨️ Cetak Laporan
        </button>
      </div>
    </div>
  );
};

export default DaftarBarangMasukPage;

