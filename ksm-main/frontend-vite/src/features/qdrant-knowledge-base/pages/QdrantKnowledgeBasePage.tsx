/**
 * Qdrant Knowledge Base Page
 * Halaman untuk manage documents, collections, dan search dengan Tailwind CSS
 */

import React, { useState, useRef } from 'react';
import {
  useGetStatisticsQuery,
  useGetDocumentsQuery,
  useGetCollectionsQuery,
  useUploadDocumentMutation,
  useDeleteDocumentMutation,
  useCreateCollectionMutation,
  useDeleteCollectionMutation,
  useSearchMutation,
} from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, Table } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { Document, Collection, SearchResult } from '../types';

const QdrantKnowledgeBasePage: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const [activeTab, setActiveTab] = useState<'dashboard' | 'documents' | 'collections' | 'search'>('dashboard');
  const [documentFilters, setDocumentFilters] = useState({
    company_id: 'PT. Kian Santang Muliatama',
    status: '',
    limit: 10,
    offset: 0,
  });
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadData, setUploadData] = useState({
    title: '',
    description: '',
    collection: 'default',
  });
  const [showNewCollectionInput, setShowNewCollectionInput] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [showCreateCollectionModal, setShowCreateCollectionModal] = useState(false);
  const [createCollectionData, setCreateCollectionData] = useState({
    name: '',
    vector_size: 1536,
    distance: 'Cosine',
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchCollection, setSearchCollection] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: statistics, refetch: refetchStats } = useGetStatisticsQuery({ 
    company_id: documentFilters.company_id 
  });
  const { data: documents = [], isLoading: documentsLoading, refetch: refetchDocuments } = useGetDocumentsQuery(documentFilters);
  const { data: collections = [], refetch: refetchCollections } = useGetCollectionsQuery();
  const [uploadDocument, { isLoading: uploading }] = useUploadDocumentMutation();
  const [deleteDocument] = useDeleteDocumentMutation();
  const [createCollection] = useCreateCollectionMutation();
  const [deleteCollection] = useDeleteCollectionMutation();
  const [search, { isLoading: searching }] = useSearchMutation();

  const handleUpload = async () => {
    if (!uploadFile) {
      await sweetAlert.showError('Error', 'Pilih file PDF terlebih dahulu');
      return;
    }

    try {
      const base64Content = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(uploadFile);
      });

      await uploadDocument({
        filename: uploadFile.name,
        base64_content: base64Content,
        company_id: documentFilters.company_id,
        title: uploadData.title || uploadFile.name,
        description: uploadData.description,
        collection: uploadData.collection,
      }).unwrap();

      await sweetAlert.showSuccessAuto('Berhasil', 'Dokumen berhasil diupload');
      setUploadFile(null);
      setUploadData({ title: '', description: '', collection: 'default' });
      refetchDocuments();
      refetchStats();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal upload dokumen');
    }
  };

  const handleDeleteDocument = async (id: number) => {
    const confirmed = await sweetAlert.showConfirm(
      'Konfirmasi Hapus',
      'Apakah Anda yakin ingin menghapus dokumen ini?',
      'warning'
    );

    if (confirmed) {
      try {
        await deleteDocument(id).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Dokumen berhasil dihapus');
        refetchDocuments();
        refetchStats();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal menghapus dokumen');
      }
    }
  };

  const handleCreateCollection = async () => {
    if (!createCollectionData.name.trim()) {
      await sweetAlert.showError('Error', 'Masukkan nama collection');
      return;
    }

    try {
      await createCollection(createCollectionData).unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Collection berhasil dibuat');
      setShowCreateCollectionModal(false);
      setCreateCollectionData({ name: '', vector_size: 1536, distance: 'Cosine' });
      refetchCollections();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal membuat collection');
    }
  };

  const handleDeleteCollection = async (name: string) => {
    const confirmed = await sweetAlert.showConfirm(
      'Konfirmasi Hapus',
      `Apakah Anda yakin ingin menghapus collection "${name}"? Semua data di dalamnya akan hilang!`,
      'warning'
    );

    if (confirmed) {
      try {
        await deleteCollection(name).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Collection berhasil dihapus');
        refetchCollections();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal menghapus collection');
      }
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim() || !searchCollection) {
      await sweetAlert.showError('Error', 'Masukkan query dan pilih collection');
      return;
    }

    try {
      const results = await search({
        query: searchQuery,
        collection_name: searchCollection,
        limit: 10,
        score_threshold: 0.7,
      }).unwrap();
      setSearchResults(results);
      if (results.length === 0) {
        await sweetAlert.showInfo('Tidak Ada Hasil', 'Tidak ditemukan dokumen yang relevan');
      }
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal melakukan pencarian');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      ready: 'bg-green-100 text-green-800',
      processing: 'bg-yellow-100 text-yellow-800',
      failed: 'bg-red-100 text-red-800',
      uploaded: 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const documentColumns = [
    {
      key: 'title',
      label: 'Document',
      render: (_value: any, item: Document) => (
        <div>
          <div className="font-medium text-gray-900">{item.original_name}</div>
          <div className="text-sm text-gray-500">{item.title}</div>
        </div>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: Document) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
          {item.status}
        </span>
      ),
    },
    {
      key: 'pages',
      label: 'Pages',
      render: (_value: any, item: Document) => item.total_pages || 0,
    },
    {
      key: 'vectors',
      label: 'Vectors',
      render: (_value: any, item: Document) => item.vector_count || 0,
    },
    {
      key: 'size',
      label: 'Size',
      render: (_value: any, item: Document) => formatFileSize(item.size_bytes || 0),
    },
    {
      key: 'created',
      label: 'Created',
      render: (_value: any, item: Document) => formatDate(item.created_at),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_value: any, item: Document) => (
        <Button
          variant="danger"
          size="sm"
          onClick={() => handleDeleteDocument(item.id)}
        >
          🗑️ Delete
        </Button>
      ),
    },
  ];

  if (documentsLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">🧠 Qdrant Knowledge Base</h1>
        <p className="text-gray-600">Manajemen dokumen RAG dengan integrasi Qdrant langsung</p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-md mb-6">
        <div className="flex border-b border-gray-200">
          {(['dashboard', 'documents', 'collections', 'search'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 font-medium text-sm ${
                activeTab === tab
                  ? 'text-primary-600 border-b-2 border-primary-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab === 'dashboard' && '📊 Dashboard'}
              {tab === 'documents' && '📄 Documents'}
              {tab === 'collections' && '🗂️ Collections'}
              {tab === 'search' && '🔍 Search'}
            </button>
          ))}
        </div>
      </div>

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && statistics && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow-md p-4">
              <div className="text-sm text-gray-600 mb-1">Total Documents</div>
              <div className="text-2xl font-bold text-gray-800">{statistics.total_documents ?? 0}</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-4">
              <div className="text-sm text-gray-600 mb-1">Collections</div>
              <div className="text-2xl font-bold text-blue-600">{statistics.total_collections ?? 0}</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-4">
              <div className="text-sm text-gray-600 mb-1">Vectors</div>
              <div className="text-2xl font-bold text-purple-600">{statistics.total_vectors ?? 0}</div>
            </div>
            <div className="bg-white rounded-lg shadow-md p-4">
              <div className="text-sm text-gray-600 mb-1">Storage (MB)</div>
              <div className="text-2xl font-bold text-orange-600">
                {statistics.total_storage_mb != null ? statistics.total_storage_mb.toFixed(1) : '0.0'}
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Document Status</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-green-500"></span>
                <span>Ready: {statistics.documents_by_status?.ready ?? 0}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                <span>Processing: {statistics.documents_by_status?.processing ?? 0}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-500"></span>
                <span>Failed: {statistics.documents_by_status?.failed ?? 0}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-gray-500"></span>
                <span>Uploaded: {statistics.documents_by_status?.uploaded ?? 0}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Documents Tab */}
      {activeTab === 'documents' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <h3 className="text-lg font-semibold text-gray-800">Document Management</h3>
              <Button
                variant="primary"
                onClick={() => fileInputRef.current?.click()}
              >
                📤 Upload PDF
              </Button>
            </div>
          </div>

          {/* Upload Modal */}
          {uploadFile && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-gray-800">Upload Document</h2>
                    <Button variant="outline" size="sm" onClick={() => setUploadFile(null)}>
                      ✕
                    </Button>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">File</label>
                      <div className="text-sm text-gray-600">{uploadFile.name}</div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Title</label>
                      <Input
                        type="text"
                        value={uploadData.title}
                        onChange={(e) => setUploadData(prev => ({ ...prev, title: e.target.value }))}
                        placeholder="Document title"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                      <textarea
                        value={uploadData.description}
                        onChange={(e) => setUploadData(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Document description"
                        rows={3}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Collection</label>
                      <select
                        value={uploadData.collection}
                        onChange={(e) => {
                          if (e.target.value === 'new') {
                            setShowNewCollectionInput(true);
                            setUploadData(prev => ({ ...prev, collection: '' }));
                          } else {
                            setShowNewCollectionInput(false);
                            setUploadData(prev => ({ ...prev, collection: e.target.value }));
                          }
                        }}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="">Select Collection</option>
                        {collections.map((collection) => (
                          <option key={collection.name} value={collection.name}>
                            {collection.name} ({collection.vectors_count} vectors)
                          </option>
                        ))}
                        <option value="new">+ Create New Collection</option>
                      </select>
                      {showNewCollectionInput && (
                        <div className="mt-2 flex gap-2">
                          <Input
                            type="text"
                            value={newCollectionName}
                            onChange={(e) => setNewCollectionName(e.target.value)}
                            placeholder="Enter new collection name"
                            className="flex-1"
                          />
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={async () => {
                              if (!newCollectionName.trim()) {
                                await sweetAlert.showError('Error', 'Masukkan nama collection');
                                return;
                              }
                              try {
                                await createCollection({
                                  collection_name: newCollectionName,
                                  vector_size: 1536,
                                  distance: 'Cosine',
                                }).unwrap();
                                await sweetAlert.showSuccessAuto('Berhasil', 'Collection berhasil dibuat');
                                setShowNewCollectionInput(false);
                                setUploadData(prev => ({ ...prev, collection: newCollectionName }));
                                setNewCollectionName('');
                                refetchCollections();
                              } catch (error: any) {
                                await sweetAlert.showError('Gagal', error?.message || 'Gagal membuat collection');
                              }
                            }}
                          >
                            Create
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex justify-end gap-4 pt-4 border-t border-gray-200 mt-4">
                    <Button variant="outline" onClick={() => setUploadFile(null)}>
                      Cancel
                    </Button>
                    <Button variant="primary" onClick={handleUpload} disabled={uploading}>
                      {uploading ? 'Uploading...' : 'Upload'}
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Filters */}
          <div className="bg-white rounded-lg shadow-md p-4">
            <select
              value={documentFilters.status}
              onChange={(e) => setDocumentFilters(prev => ({ ...prev, status: e.target.value }))}
              className="block w-full md:w-auto px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All Status</option>
              <option value="ready">Ready</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
              <option value="uploaded">Uploaded</option>
            </select>
          </div>

          {/* Documents Table */}
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <Table
              data={documents}
              columns={documentColumns}
              loading={documentsLoading}
              emptyMessage="Tidak ada dokumen ditemukan"
            />
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            style={{ display: 'none' }}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) {
                setUploadFile(file);
                setUploadData(prev => ({ ...prev, title: file.name.replace('.pdf', '') }));
              }
            }}
          />
        </div>
      )}

      {/* Collections Tab */}
      {activeTab === 'collections' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <h3 className="text-lg font-semibold text-gray-800">Collection Management</h3>
              <Button
                variant="primary"
                onClick={() => setShowCreateCollectionModal(true)}
              >
                ➕ Create Collection
              </Button>
            </div>
          </div>

          {/* Create Collection Modal */}
          {showCreateCollectionModal && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-gray-800">Create Collection</h2>
                    <Button variant="outline" size="sm" onClick={() => setShowCreateCollectionModal(false)}>
                      ✕
                    </Button>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Collection Name</label>
                      <Input
                        type="text"
                        value={createCollectionData.name}
                        onChange={(e) => setCreateCollectionData(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="e.g., PT. Kian Santang Muliatama_documents"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Vector Size</label>
                      <Input
                        type="number"
                        value={createCollectionData.vector_size}
                        onChange={(e) => setCreateCollectionData(prev => ({ ...prev, vector_size: parseInt(e.target.value) || 1536 }))}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Distance Metric</label>
                      <select
                        value={createCollectionData.distance}
                        onChange={(e) => setCreateCollectionData(prev => ({ ...prev, distance: e.target.value }))}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="Cosine">Cosine</option>
                        <option value="Euclidean">Euclidean</option>
                        <option value="Dot">Dot</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex justify-end gap-4 pt-4 border-t border-gray-200 mt-4">
                    <Button variant="outline" onClick={() => setShowCreateCollectionModal(false)}>
                      Cancel
                    </Button>
                    <Button variant="primary" onClick={handleCreateCollection}>
                      Create
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Collections Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {collections.map((collection) => (
              <div key={collection.name} className="bg-white rounded-lg shadow-md p-4">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-gray-900">{collection.name}</h4>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    collection.status === 'green' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {collection.status}
                  </span>
                </div>
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Vectors:</span>
                    <span className="font-semibold">{collection.vectors_count}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Size:</span>
                    <span className="font-semibold">{collection.config?.vector_size || 1536}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Distance:</span>
                    <span className="font-semibold">{collection.config?.distance || 'Cosine'}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleDeleteCollection(collection.name)}
                    className="flex-1"
                  >
                    🗑️ Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search Tab */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Search Query</label>
                <textarea
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Enter your search query..."
                  rows={3}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Collection</label>
                <select
                  value={searchCollection}
                  onChange={(e) => setSearchCollection(e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">Select Collection</option>
                  {collections.map((collection) => (
                    <option key={collection.name} value={collection.name}>
                      {collection.name} ({collection.vectors_count} vectors)
                    </option>
                  ))}
                </select>
              </div>
              <Button
                variant="primary"
                onClick={handleSearch}
                disabled={!searchQuery.trim() || !searchCollection || searching}
                className="w-full"
              >
                {searching ? 'Searching...' : '🔍 Search'}
              </Button>
            </div>
          </div>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Search Results ({searchResults.length})</h3>
              <div className="space-y-4">
                {searchResults.map((result) => (
                  <div key={result.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-primary-600">
                        Score: {result.score != null ? (result.score * 100).toFixed(1) : '0.0'}%
                      </span>
                      <span className="text-xs text-gray-500">Doc ID: {result.payload?.document_id ?? 'N/A'}</span>
                    </div>
                    <div className="text-sm text-gray-700 mb-2">{result.payload?.text ?? 'No text available'}</div>
                    <div className="text-xs text-gray-500">
                      Chunk {result.payload?.chunk_index ?? 'N/A'} • {result.payload?.created_at ? formatDate(result.payload.created_at) : 'N/A'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default QdrantKnowledgeBasePage;

