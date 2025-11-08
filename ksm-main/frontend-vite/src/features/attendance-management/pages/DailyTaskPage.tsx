/**
 * Daily Task Page
 * Halaman untuk mengelola task harian dengan Tailwind CSS
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetTasksQuery, useCreateTaskMutation, useUpdateTaskMutation, useDeleteTaskMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, Dropdown } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { DropdownOption } from '@/shared/components/ui';

const DailyTaskPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    search: '',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState<any>(null);
  const [optimisticUpdates, setOptimisticUpdates] = useState<Record<number, string>>({});

  const { data: tasksData, isLoading, refetch, isFetching } = useGetTasksQuery({
    ...filters,
    page: currentPage,
    per_page: itemsPerPage,
  });
  const [createTask] = useCreateTaskMutation();
  const [updateTask] = useUpdateTaskMutation();
  const [deleteTask] = useDeleteTaskMutation();

  // Merge optimistic updates dengan data dari server
  const tasks = (tasksData?.items || []).map(task => {
    if (optimisticUpdates[task.id]) {
      return { ...task, status: optimisticUpdates[task.id] as any };
    }
    return task;
  });
  const pagination = tasksData?.pagination || { page: 1, per_page: 10, total: 0, pages: 1 };

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    due_date: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.title) {
      await sweetAlert.showError('Error', 'Title harus diisi');
      return;
    }

    try {
      if (editingTask) {
        await updateTask({ id: editingTask.id, data: formData }).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Task berhasil diupdate');
      } else {
        await createTask(formData).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Task berhasil dibuat');
      }
      setShowForm(false);
      setEditingTask(null);
      setFormData({ title: '', description: '', priority: 'medium', due_date: '' });
      refetch();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal menyimpan task');
    }
  };

  const handleEdit = (task: any) => {
    setEditingTask(task);
    setFormData({
      title: task.title,
      description: task.description || '',
      priority: task.priority || 'medium',
      due_date: task.due_date || '',
    });
    setShowForm(true);
  };

  const handleDelete = async (taskId: number) => {
    const confirmed = await sweetAlert.showConfirm(
      'Konfirmasi Hapus',
      'Apakah Anda yakin ingin menghapus task ini?',
      'warning'
    );

    if (confirmed) {
      try {
        await deleteTask(taskId).unwrap();
        await sweetAlert.showSuccessAuto('Berhasil', 'Task berhasil dihapus');
        refetch();
      } catch (error: any) {
        await sweetAlert.showError('Gagal', error?.message || 'Gagal menghapus task');
      }
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'pending': return 'Pending';
      case 'in_progress': return 'In Progress';
      case 'completed': return 'Selesai';
      case 'cancelled': return 'Dibatalkan';
      default: return status;
    }
  };

  const handleStatusChange = async (taskId: number, newStatus: string) => {
    console.log('🔄 handleStatusChange called:', { taskId, newStatus });
    
    // Optimistic update - update UI langsung
    setOptimisticUpdates(prev => {
      const updated = { ...prev, [taskId]: newStatus };
      console.log('✅ Optimistic update set:', updated);
      return updated;
    });
    
    try {
      // Update ke server - RTK Query akan otomatis invalidate cache dan trigger refetch
      console.log('📡 Updating task to server...');
      const updateResult = await updateTask({ id: taskId, data: { status: newStatus } }).unwrap();
      console.log('✅ Update result:', updateResult);
      
      // Verifikasi bahwa response dari server menunjukkan status sudah ter-update
      if (updateResult && updateResult.status !== newStatus) {
        console.error('❌ Server response status tidak sesuai:', updateResult.status, 'expected:', newStatus);
        throw new Error('Status tidak ter-update di server. Response: ' + JSON.stringify(updateResult));
      }
      
      // Tunggu sebentar untuk memastikan cache ter-invalidate
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // Refetch data terbaru dari server dengan retry mechanism
      let retryCount = 0;
      let updatedTask = null;
      const maxRetries = 5;
      
      while (retryCount < maxRetries) {
        console.log(`🔄 Refetching data (attempt ${retryCount + 1}/${maxRetries})...`);
        const refetchResult = await refetch();
        updatedTask = refetchResult.data?.items?.find(t => t.id === taskId);
        console.log('🔍 Updated task found:', updatedTask);
        
        // Jika data sudah ter-update dengan benar, keluar dari loop
        if (updatedTask && updatedTask.status === newStatus) {
          console.log('✅ Data confirmed updated!');
          break;
        }
        
        // Jika belum ter-update, tunggu sebentar dan coba lagi
        retryCount++;
        if (retryCount < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, 400));
        }
      }
      
      // Hapus optimistic update HANYA jika data sudah terkonfirmasi ter-update
      // Gunakan data dari updateResult sebagai sumber kebenaran utama
      const confirmedStatus = updateResult?.status || updatedTask?.status;
      
      if (confirmedStatus === newStatus) {
        // Tunggu sedikit lagi untuk memastikan database commit sudah selesai
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Verifikasi sekali lagi dengan refetch sebelum menghapus optimistic update
        const finalVerification = await refetch();
        const finalTask = finalVerification.data?.items?.find(t => t.id === taskId);
        
        if (finalTask && finalTask.status === newStatus) {
          // Data sudah terkonfirmasi ter-update, hapus optimistic update
          setOptimisticUpdates(prev => {
            const newUpdates = { ...prev };
            delete newUpdates[taskId];
            console.log('🧹 Removed optimistic update for task:', taskId, 'Final status:', finalTask.status);
            return newUpdates;
          });
          await sweetAlert.showSuccessAuto('Berhasil', `Status task berhasil diubah menjadi ${getStatusLabel(newStatus)}`);
        } else {
          // Jika setelah verifikasi akhir masih belum ter-update, pertahankan optimistic update
          console.warn('⚠️ Final verification failed, keeping optimistic update. Expected:', newStatus, 'Got:', finalTask?.status);
          await sweetAlert.showSuccessAuto('Berhasil', `Status task berhasil diubah menjadi ${getStatusLabel(newStatus)}`);
          // Coba lagi setelah beberapa detik
          setTimeout(async () => {
            const delayedRefetch = await refetch();
            const delayedCheck = delayedRefetch.data?.items?.find(t => t.id === taskId);
            if (delayedCheck && delayedCheck.status === newStatus) {
              setOptimisticUpdates(prev => {
                const newUpdates = { ...prev };
                delete newUpdates[taskId];
                console.log('🧹 Removed optimistic update after delayed check');
                return newUpdates;
              });
            }
          }, 2000);
        }
      } else {
        // Jika setelah beberapa retry masih belum ter-update, tetap pertahankan optimistic update
        // dan tampilkan notifikasi (mungkin ada delay di server)
        console.warn('⚠️ Data belum ter-update setelah beberapa retry, keeping optimistic update');
        await sweetAlert.showSuccessAuto('Berhasil', `Status task berhasil diubah menjadi ${getStatusLabel(newStatus)}`);
        // Refetch sekali lagi secara async untuk memastikan
        setTimeout(async () => {
          const finalRefetch = await refetch();
          const finalCheck = finalRefetch.data?.items?.find(t => t.id === taskId);
          if (finalCheck && finalCheck.status === newStatus) {
            setOptimisticUpdates(prev => {
              const newUpdates = { ...prev };
              delete newUpdates[taskId];
              return newUpdates;
            });
          }
        }, 2000);
      }
    } catch (error: any) {
      console.error('❌ Error updating task status:', error);
      // Rollback optimistic update jika gagal
      setOptimisticUpdates(prev => {
        const newUpdates = { ...prev };
        delete newUpdates[taskId];
        return newUpdates;
      });
      await sweetAlert.showError('Gagal', error?.message || 'Gagal mengubah status task');
      // Refetch untuk memastikan data konsisten dengan server
      await refetch();
    }
  };

  const getStatusOptions = (currentStatus: string): DropdownOption[] => {
    const allStatuses: Array<{ value: string; label: string; icon: string }> = [
      { value: 'pending', label: 'Pending', icon: '⏳' },
      { value: 'in_progress', label: 'In Progress', icon: '🔄' },
      { value: 'completed', label: 'Selesai', icon: '✓' },
      { value: 'cancelled', label: 'Dibatalkan', icon: '✕' },
    ];

    return allStatuses.map(status => ({
      value: status.value,
      label: status.label,
      icon: status.icon,
      disabled: status.value === currentStatus,
    }));
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
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
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📋 Daily Task</h1>
            <p className="text-gray-600">Kelola task harian Anda</p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="primary"
              onClick={() => {
                setShowForm(true);
                setEditingTask(null);
                setFormData({ title: '', description: '', priority: 'medium', due_date: '' });
              }}
            >
              ➕ Tambah Task
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate('/attendance/dashboard')}
            >
              ← Kembali
            </Button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Input
              type="text"
              placeholder="Cari task..."
              value={filters.search}
              onChange={(e) => {
                setFilters(prev => ({ ...prev, search: e.target.value }));
                setCurrentPage(1);
              }}
            />
          </div>
          <div>
            <select
              value={filters.status}
              onChange={(e) => {
                setFilters(prev => ({ ...prev, status: e.target.value }));
                setCurrentPage(1);
              }}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Semua Status</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div>
            <select
              value={filters.priority}
              onChange={(e) => {
                setFilters(prev => ({ ...prev, priority: e.target.value }));
                setCurrentPage(1);
              }}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Semua Priority</option>
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Task Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-800">
                  {editingTask ? 'Edit Task' : 'Tambah Task'}
                </h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setShowForm(false);
                    setEditingTask(null);
                    setFormData({ title: '', description: '', priority: 'medium', due_date: '' });
                  }}
                >
                  ✕
                </Button>
              </div>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Title *</label>
                  <Input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    rows={4}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-vertical"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
                    <select
                      value={formData.priority}
                      onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value }))}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Due Date</label>
                    <Input
                      type="date"
                      value={formData.due_date}
                      onChange={(e) => setFormData(prev => ({ ...prev, due_date: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-4 pt-4 border-t border-gray-200">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowForm(false);
                      setEditingTask(null);
                      setFormData({ title: '', description: '', priority: 'medium', due_date: '' });
                    }}
                  >
                    Batal
                  </Button>
                  <Button type="submit" variant="primary">
                    {editingTask ? 'Update' : 'Simpan'}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Tasks List */}
      <div className="space-y-4">
        {tasks.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Belum Ada Task</h3>
            <p className="text-gray-600 mb-4">Klik "Tambah Task" untuk membuat task baru</p>
          </div>
        ) : (
          tasks.map(task => (
            <div key={`task-${task.id}-${task.status}`} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">{task.title}</h3>
                  {task.description && (
                    <p className="text-sm text-gray-600 mb-2">{task.description}</p>
                  )}
                  <div className="flex gap-2 flex-wrap">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(task.priority || 'medium')}`}>
                      {task.priority || 'medium'}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                      {getStatusLabel(task.status)}
                    </span>
                    {task.due_date && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs">
                        Due: {new Date(task.due_date).toLocaleDateString('id-ID')}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex flex-col sm:flex-row gap-2">
                  <div className="w-full sm:w-auto min-w-[140px]">
                    <Dropdown
                      key={`status-dropdown-${task.id}-${task.status}`}
                      options={getStatusOptions(task.status)}
                      value={task.status}
                      onChange={(value) => handleStatusChange(task.id, value as string)}
                      className="w-full"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEdit(task)}
                      className="flex-1 sm:flex-none"
                    >
                      ✏️ Edit
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDelete(task.id)}
                      className="flex-1 sm:flex-none"
                    >
                      🗑️ Hapus
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="bg-white rounded-lg shadow-md p-4 mt-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              Menampilkan {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, pagination.total)} dari {pagination.total} task
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
              >
                ←
              </Button>
              <span className="px-4 py-2 text-sm text-gray-700">
                {currentPage} / {pagination.pages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.min(pagination.pages, prev + 1))}
                disabled={currentPage === pagination.pages}
              >
                →
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DailyTaskPage;

