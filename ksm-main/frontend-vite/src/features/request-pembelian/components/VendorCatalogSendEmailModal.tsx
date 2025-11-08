/**
 * Vendor Catalog Send Email Modal Component
 * Modal untuk mengirim email ke vendor terkait item
 */

import React, { useState, useEffect, useRef } from 'react';
import { Modal, Button, Input } from '@/shared/components/ui';
import { useSendVendorEmailMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { XMarkIcon } from '@heroicons/react/24/outline';
import Swal from 'sweetalert2';
import EmailDomainConfigTab from './EmailDomainConfigTab';
import { useGetDomainConfigsQuery } from '../services/emailDomainApi';
import type { DomainConfig } from '../services/emailDomainApi';

interface VendorCatalogSendEmailModalProps {
  isOpen: boolean;
  onClose: () => void;
  item: any | null;
  onSendSuccess?: () => void;
}

const VendorCatalogSendEmailModal: React.FC<VendorCatalogSendEmailModalProps> = ({
  isOpen,
  onClose,
  item,
  onSendSuccess,
}) => {
  const sweetAlert = useSweetAlert();
  const [sendEmail, { isLoading }] = useSendVendorEmailMutation();
  const { data: domainConfigsResponse } = useGetDomainConfigsQuery();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeTab, setActiveTab] = useState<'form' | 'preview' | 'config'>('form');
  const [selectedDomainId, setSelectedDomainId] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    subject: '',
    custom_message: '',
    cc_emails: '',
    bcc_emails: '',
  });

  const domainConfigs = (domainConfigsResponse?.data as DomainConfig[]) || [];
  const defaultDomain = domainConfigs.find((d) => d.is_default && d.is_active);
  
  // Set default domain on mount
  useEffect(() => {
    if (defaultDomain && !selectedDomainId) {
      setSelectedDomainId(defaultDomain.id);
    }
  }, [defaultDomain, selectedDomainId]);

  // Helper function to create plain text table without lines, just spacing
  const createPlainTextTable = (itemName: string, quantity: string, kategori: string) => {
    // Calculate column widths based on content
    const col1Width = Math.max(15, 'Nama Barang'.length, itemName.length);
    const col2Width = Math.max(12, 'Quantity'.length, quantity.length);
    const col3Width = Math.max(12, 'Kategori'.length, kategori.length);
    
    // Create header row with proper spacing
    const header1 = 'Nama Barang'.padEnd(col1Width);
    const header2 = 'Quantity'.padEnd(col2Width);
    const header3 = 'Kategori'.padEnd(col3Width);
    
    // Create data row with proper spacing
    const data1 = itemName.padEnd(col1Width);
    const data2 = quantity.padEnd(col2Width);
    const data3 = kategori.padEnd(col3Width);
    
    return `${header1}${header2}${header3}
${data1}${data2}${data3}`;
  };

  useEffect(() => {
    if (item) {
      const vendorName = item.vendor?.company_name || 'Vendor';
      const itemName = item.nama_barang || item.request_item?.nama_barang || 'Barang';
      const quantity = item.vendor_quantity || 0;
      const satuan = item.satuan || 'pcs';
      const kategori = item.kategori || '-';
      
      // Generate plain text message with table (no HTML, no lines)
      const table = createPlainTextTable(itemName, `${quantity} ${satuan}`, kategori);
      
      const textMessage = `Halo ${vendorName},

Kami ingin meminta penawaran untuk item berikut:

${table}

Mohon kirimkan penawaran terbaik Anda.

Terima kasih.`;
      
      setFormData({
        subject: `Permintaan Penawaran - ${itemName}`,
        custom_message: textMessage,
        cc_emails: '',
        bcc_emails: '',
      });
      setSelectedFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [item]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    // Validate files
    const allowedExtensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar', '.txt', '.csv'];
    const maxSizeMB = 50;
    const maxSizeBytes = maxSizeMB * 1024 * 1024;

    const validFiles: File[] = [];
    const errors: string[] = [];

    files.forEach(file => {
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!allowedExtensions.includes(fileExtension)) {
        errors.push(`${file.name}: Format file tidak didukung`);
        return;
      }
      if (file.size > maxSizeBytes) {
        errors.push(`${file.name}: Ukuran file melebihi ${maxSizeMB}MB`);
        return;
      }
      validFiles.push(file);
    });

    if (errors.length > 0) {
      sweetAlert.showError('Error Validasi File', errors.join('\n'));
    }

    if (validFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...validFiles]);
    }
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  // Function to render email preview
  const renderEmailPreview = () => {
    if (!item) return null;

    // Parse the custom message to extract table and text
    const message = formData.custom_message;
    const lines = message.split('\n');
    
    // Find table section
    let tableFound = false;
    let tableStartIndex = -1;
    let tableEndIndex = -1;
    
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('Nama Barang') && lines[i].includes('Quantity')) {
        tableFound = true;
        tableStartIndex = i;
        // Table usually has 2 rows (header + data)
        tableEndIndex = i + 1;
        break;
      }
    }

    // Split message into parts
    const beforeTable = tableFound ? lines.slice(0, tableStartIndex).join('\n') : '';
    const tableRows = tableFound ? lines.slice(tableStartIndex, tableEndIndex + 1) : [];
    const afterTable = tableFound ? lines.slice(tableEndIndex + 1).join('\n') : '';

    // Parse table rows
    const headerRow = tableRows[0] || '';
    const dataRow = tableRows[1] || '';

    // Extract column values from header and data (assuming fixed width columns)
    const extractColumns = (row: string) => {
      if (!row.trim()) {
        return { col1: '', col2: '', col3: '' };
      }
      
      // Calculate column widths based on the original table creation logic
      const itemName = item.nama_barang || item.request_item?.nama_barang || 'Barang';
      const quantity = `${item.vendor_quantity || 0} ${item.satuan || 'pcs'}`;
      
      const col1Width = Math.max(15, 'Nama Barang'.length, itemName.length);
      const col2Width = Math.max(12, 'Quantity'.length, quantity.length);
      
      // Extract by fixed width positions
      const col1 = row.substring(0, col1Width).trim();
      const col2 = row.substring(col1Width, col1Width + col2Width).trim();
      const col3 = row.substring(col1Width + col2Width).trim();
      
      return { col1, col2, col3 };
    };

    const headerCols = extractColumns(headerRow);
    const dataCols = extractColumns(dataRow);

    return (
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Email Header */}
        <div className="bg-gradient-to-r from-primary-600 to-primary-700 text-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold mb-1">{formData.subject || 'Permintaan Penawaran'}</h2>
              <p className="text-primary-100 text-sm">KSM Procurement System</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-primary-100">Kepada:</p>
              <p className="font-semibold">{item.vendor?.email || '-'}</p>
            </div>
          </div>
        </div>

        {/* Email Body */}
        <div className="p-6 bg-gray-50">
          <div className="bg-white rounded-lg shadow-sm p-6">
            {/* Before table text */}
            {beforeTable && (
              <div className="mb-6 text-gray-700 whitespace-pre-line leading-relaxed">
                {beforeTable}
              </div>
            )}

            {/* Table */}
            {tableFound && (
              <div className="mb-6 overflow-x-auto">
                <div className="inline-block min-w-full">
                  <div className="bg-white rounded-lg overflow-hidden shadow-lg border border-gray-300">
                    {/* Table Header */}
                    <div className="bg-primary-600 border-b border-primary-700">
                      <div className="grid grid-cols-3 gap-0">
                        <div className="px-6 py-4 text-center">
                          <span className="text-white font-bold text-sm uppercase tracking-wide">
                            {headerCols.col1 || 'Nama Barang'}
                          </span>
                        </div>
                        <div className="px-6 py-4 text-center border-l border-primary-700">
                          <span className="text-white font-bold text-sm uppercase tracking-wide">
                            {headerCols.col2 || 'Quantity'}
                          </span>
                        </div>
                        <div className="px-6 py-4 text-center border-l border-primary-700">
                          <span className="text-white font-bold text-sm uppercase tracking-wide">
                            {headerCols.col3 || 'Kategori'}
                          </span>
                        </div>
                      </div>
                    </div>
                    {/* Table Data */}
                    <div className="bg-white">
                      <div className="grid grid-cols-3 gap-0">
                        <div className="px-6 py-4 text-left border-b border-gray-200">
                          <span className="text-gray-800 text-sm">
                            {dataCols.col1 || item.nama_barang || item.request_item?.nama_barang || '-'}
                          </span>
                        </div>
                        <div className="px-6 py-4 text-left border-l border-b border-gray-200">
                          <span className="text-gray-800 text-sm">
                            {dataCols.col2 || `${item.vendor_quantity || 0} ${item.satuan || 'pcs'}`}
                          </span>
                        </div>
                        <div className="px-6 py-4 text-left border-l border-b border-gray-200">
                          <span className="text-gray-800 text-sm">
                            {dataCols.col3 || item.kategori || '-'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* After table text */}
            {afterTable && (
              <div className="text-gray-700 whitespace-pre-line leading-relaxed">
                {afterTable}
              </div>
            )}

            {/* Attachments info */}
            {selectedFiles.length > 0 && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <p className="text-sm font-semibold text-gray-700 mb-2">📎 Lampiran ({selectedFiles.length} file):</p>
                <div className="space-y-1">
                  {selectedFiles.map((file, index) => (
                    <p key={index} className="text-sm text-gray-600">
                      • {file.name} ({formatFileSize(file.size)})
                    </p>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Email Footer */}
        <div className="bg-gray-100 border-t border-gray-200 p-4">
          <p className="text-xs text-gray-500 text-center">
            Email ini dikirim secara otomatis dari KSM Procurement System
          </p>
        </div>
      </div>
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!item) return;

    try {
      Swal.fire({
        title: 'Mengirim email...',
        text: selectedFiles.length > 0 ? 'Sedang mengupload file dan mengirim email...' : 'Sedang mengirim email ke vendor...',
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
          Swal.showLoading();
        },
      });

      const token = localStorage.getItem('KSM_access_token');
      const apiUrl = import.meta.env.VITE_APP_API_URL || 'http://localhost:8000';
      const attachmentIds: number[] = [];

      // Upload files if any
      if (selectedFiles.length > 0) {
        for (const file of selectedFiles) {
          try {
            const uploadFormData = new FormData();
            uploadFormData.append('file', file);
            if (item.request?.id) {
              uploadFormData.append('request_pembelian_id', item.request.id.toString());
            }
            uploadFormData.append('email_subject', formData.subject);
            uploadFormData.append('email_recipient', item.vendor?.email || '');

            const uploadResponse = await fetch(`${apiUrl}/api/email/upload-attachment`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
              },
              body: uploadFormData,
            });

            const uploadResult = await uploadResponse.json();
            if (uploadResult.success && uploadResult.data?.id) {
              attachmentIds.push(uploadResult.data.id);
            } else {
              throw new Error(uploadResult.message || 'Gagal mengupload file');
            }
          } catch (error: any) {
            Swal.close();
            await sweetAlert.showError('Gagal Upload File', error?.message || `Gagal mengupload file: ${file.name}`);
            return;
          }
        }
      }

      // Send email with attachments if any
      const emailData: any = {
        vendor_email: item.vendor?.email || '',
        vendor_name: item.vendor?.company_name || 'Vendor',
        items: [{
          nama_barang: item.nama_barang || item.request_item?.nama_barang || '',
          quantity: item.vendor_quantity || 0,
          satuan: item.satuan || 'pcs',
          kategori: item.kategori || '',
          spesifikasi: item.vendor_specifications || '',
          harga_satuan: item.vendor_unit_price || 0,
          harga_total: item.vendor_total_price || 0,
        }],
        subject: formData.subject,
        custom_message: formData.custom_message,
        cc_emails: formData.cc_emails ? formData.cc_emails.split(',').map(email => email.trim()).filter(email => email) : [],
        bcc_emails: formData.bcc_emails ? formData.bcc_emails.split(',').map(email => email.trim()).filter(email => email) : [],
      };

      // Use email domain endpoint if domain is selected
      if (selectedDomainId) {
        emailData.domain_id = selectedDomainId;
        if (attachmentIds.length > 0) {
          emailData.attachment_ids = attachmentIds;
        }
        
        // Use email-domain/send endpoint
        const response = await fetch(`${apiUrl}/api/email-domain/send`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(emailData),
        });

        const result = await response.json();

        Swal.close();
        if (result.success) {
          await sweetAlert.showSuccessAuto(
            'Berhasil',
            `Email ${attachmentIds.length > 0 ? `dengan ${attachmentIds.length} file attachment ` : ''}berhasil dikirim ke vendor via domain`
          );
          if (onSendSuccess) {
            onSendSuccess();
          }
          onClose();
        } else {
          await sweetAlert.showError('Gagal', result.message || 'Gagal mengirim email');
        }
      } else {
        // Use regular email endpoint (system default)
        // Use endpoint with attachments if files are uploaded
        if (attachmentIds.length > 0) {
          emailData.attachment_ids = attachmentIds;
          
          // Use send-vendor-email-with-attachments endpoint
          const response = await fetch(`${apiUrl}/api/email/send-vendor-email-with-attachments`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(emailData),
          });

          const result = await response.json();

          Swal.close();
          if (result.success) {
            await sweetAlert.showSuccessAuto('Berhasil', `Email dengan ${attachmentIds.length} file attachment berhasil dikirim ke vendor`);
            if (onSendSuccess) {
              onSendSuccess();
            }
            onClose();
          } else {
            await sweetAlert.showError('Gagal', result.message || 'Gagal mengirim email');
          }
        } else {
          // Use regular send email endpoint
          const response = await sendEmail(emailData).unwrap();

          Swal.close();
          if (response.success) {
            await sweetAlert.showSuccessAuto('Berhasil', 'Email berhasil dikirim ke vendor');
            if (onSendSuccess) {
              onSendSuccess();
            }
            onClose();
          } else {
            await sweetAlert.showError('Gagal', response.message || 'Gagal mengirim email');
          }
        }
      }
    } catch (error: any) {
      Swal.close();
      await sweetAlert.showError('Gagal', error?.data?.message || error?.message || 'Gagal mengirim email');
    }
  };

  if (!item) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Kirim Email ke Vendor"
      size="xl"
    >
      {/* Tab Navigation */}
      <div className="mb-4 border-b border-gray-200">
        <nav className="flex space-x-4">
          <button
            type="button"
            onClick={() => setActiveTab('form')}
            className={`py-2 px-4 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'form'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📝 Form Email
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('preview')}
            className={`py-2 px-4 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'preview'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            👁️ Preview Email
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('config')}
            className={`py-2 px-4 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'config'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            ⚙️ Konfigurasi Email
          </button>
        </nav>
      </div>

      {activeTab === 'form' && (
        <form onSubmit={handleSubmit} className="space-y-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <p className="text-sm text-gray-700">
            <span className="font-semibold">Kepada:</span> {item.vendor?.email || '-'}
          </p>
          <p className="text-sm text-gray-700 mt-1">
            <span className="font-semibold">Vendor:</span> {item.vendor?.company_name || '-'}
          </p>
          <p className="text-sm text-gray-700 mt-1">
            <span className="font-semibold">Item:</span> {item.nama_barang || item.request_item?.nama_barang || '-'}
          </p>
        </div>

        {/* Email Domain Selection */}
        {domainConfigs.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Domain (Opsional)
            </label>
            <select
              value={selectedDomainId || ''}
              onChange={(e) => setSelectedDomainId(e.target.value ? parseInt(e.target.value) : null)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Gunakan default sistem</option>
              {domainConfigs
                .filter((d) => d.is_active)
                .map((domain) => (
                  <option key={domain.id} value={domain.id}>
                    {domain.domain_name} {domain.is_default && '(Default)'}
                  </option>
                ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Pilih email domain yang akan digunakan untuk mengirim email. Jika tidak dipilih, akan menggunakan konfigurasi default sistem.
            </p>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Subject *
          </label>
          <Input
            type="text"
            name="subject"
            value={formData.subject}
            onChange={handleChange}
            placeholder="Subject email"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Pesan *
          </label>
          <textarea
            name="custom_message"
            value={formData.custom_message}
            onChange={handleChange}
            placeholder="Tulis pesan untuk vendor..."
            rows={12}
            className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Tabel informasi item sudah disertakan. Anda dapat menambahkan atau mengedit teks lainnya sesuai kebutuhan.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              CC (pisahkan dengan koma)
            </label>
            <Input
              type="text"
              name="cc_emails"
              value={formData.cc_emails}
              onChange={handleChange}
              placeholder="email1@example.com, email2@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              BCC (pisahkan dengan koma)
            </label>
            <Input
              type="text"
              name="bcc_emails"
              value={formData.bcc_emails}
              onChange={handleChange}
              placeholder="email1@example.com, email2@example.com"
            />
          </div>
        </div>

        {/* Upload File Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload File (Opsional)
          </label>
          <div className="space-y-2">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileSelect}
              accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.gif,.zip,.rar,.txt,.csv"
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 cursor-pointer"
              disabled={isLoading}
            />
            {selectedFiles.length > 0 && (
              <div className="space-y-2 mt-2">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg"
                  >
                    <div className="flex-1">
                      <p className="text-sm font-medium text-green-800">{file.name}</p>
                      <p className="text-xs text-green-600 mt-1">
                        Ukuran: {formatFileSize(file.size)}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveFile(index)}
                      className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="Hapus file"
                    >
                      <XMarkIcon className="w-5 h-5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Format yang didukung: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, JPG, PNG, ZIP, RAR, TXT, CSV. Maksimal 50MB per file.
          </p>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <p className="text-xs text-yellow-800">
            <strong>Catatan:</strong> Email akan dikirim ke vendor dengan informasi item yang dipilih.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-end pt-4 border-t border-gray-200">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={isLoading}
          >
            Batal
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={isLoading || !item.vendor?.email}
            className="flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <span className="animate-spin">⏳</span>
                Mengirim...
              </>
            ) : (
              <>
                <span>📧</span>
                Kirim Email
              </>
            )}
          </Button>
        </div>
      </form>
      )}

      {activeTab === 'preview' && (
        <div className="space-y-4">
          {/* Preview Section */}
          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <p className="text-sm text-gray-600 mb-2">
              <span className="font-semibold">Kepada:</span> {item.vendor?.email || '-'}
            </p>
            <p className="text-sm text-gray-600 mb-2">
              <span className="font-semibold">Vendor:</span> {item.vendor?.company_name || '-'}
            </p>
            {formData.cc_emails && (
              <p className="text-sm text-gray-600 mb-2">
                <span className="font-semibold">CC:</span> {formData.cc_emails}
              </p>
            )}
            {formData.bcc_emails && (
              <p className="text-sm text-gray-600">
                <span className="font-semibold">BCC:</span> {formData.bcc_emails}
              </p>
            )}
          </div>

          {/* Email Preview */}
          <div className="max-h-[600px] overflow-y-auto">
            {renderEmailPreview()}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-end pt-4 border-t border-gray-200">
            <Button
              type="button"
              variant="outline"
              onClick={() => setActiveTab('form')}
            >
              ← Kembali ke Form
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isLoading}
            >
              Batal
            </Button>
            <Button
              type="button"
              variant="primary"
              onClick={async (e) => {
                e.preventDefault();
                // Create a synthetic form event and submit
                const syntheticEvent = new Event('submit', { bubbles: true, cancelable: true });
                await handleSubmit(syntheticEvent as any);
              }}
              disabled={isLoading || !item.vendor?.email}
              className="flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <span className="animate-spin">⏳</span>
                  Mengirim...
                </>
              ) : (
                <>
                  <span>📧</span>
                  Kirim Email
                </>
              )}
            </Button>
          </div>
        </div>
      )}

      {activeTab === 'config' && (
        <EmailDomainConfigTab
          onDomainSelect={(domainId) => {
            setSelectedDomainId(domainId);
            if (domainId) {
              // Switch to form tab after selecting domain
              setActiveTab('form');
            }
          }}
          selectedDomainId={selectedDomainId}
        />
      )}
    </Modal>
  );
};

export default VendorCatalogSendEmailModal;

