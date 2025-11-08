/**
 * Enhanced Notion Tasks Page
 * Halaman untuk menampilkan dan mengelola task dari Notion dengan Tailwind CSS
 */

import React, { useState, useMemo } from 'react';
import {
  useGetTasksQuery,
  useGetStatisticsQuery,
  useGetEmployeesQuery,
  useSyncTasksMutation,
} from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input, Table } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { NotionTask } from '../types';

const EnhancedNotionTasksPage: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const [filter, setFilter] = useState({
    employee: '',
    status: '',
    priority: '',
    date_from: '',
    date_to: '',
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const { data: tasks = [], isLoading, refetch } = useGetTasksQuery(filter);
  const { data: statistics, refetch: refetchStats } = useGetStatisticsQuery();
  const { data: employees = [], refetch: refetchEmployees } = useGetEmployeesQuery();
  
  // Default statistics untuk menghindari error
  const safeStatistics = statistics || {
    total_employees: 0,
    total_tasks: 0,
    tasks_by_status: {},
    tasks_by_priority: {},
    last_sync: new Date().toISOString(),
  };
  const [syncTasks, { isLoading: syncing }] = useSyncTasksMutation();

  const handleSync = async () => {
    try {
      await syncTasks().unwrap();
      await sweetAlert.showSuccessAuto('Berhasil', 'Task berhasil disinkronkan');
      refetch();
      refetchStats();
      refetchEmployees();
    } catch (error: any) {
      await sweetAlert.showError('Gagal', error?.message || 'Gagal sinkronisasi task');
    }
  };

  const filteredAndSortedTasks = useMemo(() => {
    // Pastikan tasks selalu array
    const tasksArray = Array.isArray(tasks) ? tasks : [];
    
    let filtered = tasksArray.filter((task) => {
      const matchesSearch =
        !searchTerm ||
        task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        task.employee_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        task.description?.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesSearch;
    });

    // Sort
    filtered.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortBy) {
        case 'date':
          aValue = new Date(a.date).getTime();
          bValue = new Date(b.date).getTime();
          break;
        case 'title':
          aValue = a.title.toLowerCase();
          bValue = b.title.toLowerCase();
          break;
        case 'employee':
          aValue = a.employee_name.toLowerCase();
          bValue = b.employee_name.toLowerCase();
          break;
        case 'status':
          aValue = a.status.toLowerCase();
          bValue = b.status.toLowerCase();
          break;
        case 'priority':
          aValue = a.priority.toLowerCase();
          bValue = b.priority.toLowerCase();
          break;
        default:
          return 0;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [tasks, searchTerm, sortBy, sortOrder]);

  const getStatusColor = (status: string) => {
    const statusColors: Record<string, string> = {
      'Not Started': 'bg-gray-100 text-gray-800',
      'In Progress': 'bg-blue-100 text-blue-800',
      'Done': 'bg-green-100 text-green-800',
      'Blocked': 'bg-red-100 text-red-800',
      'Cancelled': 'bg-gray-100 text-gray-600',
    };
    return statusColors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityColor = (priority: string) => {
    const priorityColors: Record<string, string> = {
      'Low': 'bg-green-100 text-green-800',
      'Medium': 'bg-yellow-100 text-yellow-800',
      'High': 'bg-orange-100 text-orange-800',
      'Urgent': 'bg-red-100 text-red-800',
    };
    return priorityColors[priority] || 'bg-gray-100 text-gray-800';
  };

  const columns = [
    {
      key: 'title',
      label: 'Judul Task',
      render: (_value: any, item: NotionTask) => (
        <div>
          <div className="font-medium text-gray-900">{item.title}</div>
          {item.description && (
            <div className="text-sm text-gray-500 mt-1 line-clamp-2">{item.description}</div>
          )}
        </div>
      ),
    },
    {
      key: 'employee_name',
      label: 'Employee',
      render: (_value: any, item: NotionTask) => (
        <span className="font-medium">{item.employee_name}</span>
      ),
    },
    {
      key: 'date',
      label: 'Tanggal',
      render: (_value: any, item: NotionTask) => {
        const date = new Date(item.date);
        return date.toLocaleDateString('id-ID', { year: 'numeric', month: 'long', day: 'numeric' });
      },
    },
    {
      key: 'status',
      label: 'Status',
      render: (_value: any, item: NotionTask) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
          {item.status}
        </span>
      ),
    },
    {
      key: 'priority',
      label: 'Priority',
      render: (_value: any, item: NotionTask) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(item.priority)}`}>
          {item.priority}
        </span>
      ),
    },
    {
      key: 'notion_url',
      label: 'Link',
      render: (_value: any, item: NotionTask) => (
        <a
          href={item.notion_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary-600 hover:text-primary-800 underline text-sm"
        >
          Buka di Notion
        </a>
      ),
    },
  ];

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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📋 Enhanced Notion Tasks</h1>
            <p className="text-gray-600">Kelola dan monitor task dari Notion</p>
          </div>
          <Button
            variant="primary"
            onClick={handleSync}
            disabled={syncing}
          >
            {syncing ? '⏳ Sinkronisasi...' : '🔄 Sinkronisasi Task'}
          </Button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="text-sm text-gray-600 mb-1">Total Employees</div>
          <div className="text-2xl font-bold text-gray-800">{safeStatistics.total_employees}</div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="text-sm text-gray-600 mb-1">Total Tasks</div>
          <div className="text-2xl font-bold text-blue-600">{safeStatistics.total_tasks}</div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="text-sm text-gray-600 mb-1">By Status</div>
          <div className="text-xs text-gray-500">
            {safeStatistics.tasks_by_status && typeof safeStatistics.tasks_by_status === 'object' && Object.keys(safeStatistics.tasks_by_status).length > 0
              ? Object.entries(safeStatistics.tasks_by_status).map(([status, count]) => (
                  <div key={status} className="flex justify-between">
                    <span>{status}:</span>
                    <span className="font-semibold">{count}</span>
                  </div>
                ))
              : <span className="text-gray-400">Tidak ada data</span>
            }
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="text-sm text-gray-600 mb-1">By Priority</div>
          <div className="text-xs text-gray-500">
            {safeStatistics.tasks_by_priority && typeof safeStatistics.tasks_by_priority === 'object' && Object.keys(safeStatistics.tasks_by_priority).length > 0
              ? Object.entries(safeStatistics.tasks_by_priority).map(([priority, count]) => (
                  <div key={priority} className="flex justify-between">
                    <span>{priority}:</span>
                    <span className="font-semibold">{count}</span>
                  </div>
                ))
              : <span className="text-gray-400">Tidak ada data</span>
            }
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <div className="text-sm text-gray-600 mb-1">Last Sync</div>
          <div className="text-xs text-gray-500">
            {safeStatistics.last_sync 
              ? new Date(safeStatistics.last_sync).toLocaleString('id-ID')
              : <span className="text-gray-400">Belum ada sync</span>
            }
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
          <div className="md:col-span-2">
            <Input
              type="text"
              placeholder="Cari task..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div>
            <select
              value={filter.employee}
              onChange={(e) => setFilter(prev => ({ ...prev, employee: e.target.value }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Semua Employee</option>
              {employees.map((emp) => (
                <option key={emp.name} value={emp.name}>
                  {emp.name} ({emp.task_count})
                </option>
              ))}
            </select>
          </div>
          <div>
            <select
              value={filter.status}
              onChange={(e) => setFilter(prev => ({ ...prev, status: e.target.value }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Semua Status</option>
              <option value="Not Started">Not Started</option>
              <option value="In Progress">In Progress</option>
              <option value="Done">Done</option>
              <option value="Blocked">Blocked</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
          <div>
            <select
              value={filter.priority}
              onChange={(e) => setFilter(prev => ({ ...prev, priority: e.target.value }))}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Semua Priority</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Urgent">Urgent</option>
            </select>
          </div>
          <div>
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split('-');
                setSortBy(field);
                setSortOrder(order as 'asc' | 'desc');
              }}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="date-desc">Sort: Tanggal (Terbaru)</option>
              <option value="date-asc">Sort: Tanggal (Terlama)</option>
              <option value="title-asc">Sort: Judul (A-Z)</option>
              <option value="title-desc">Sort: Judul (Z-A)</option>
              <option value="employee-asc">Sort: Employee (A-Z)</option>
              <option value="status-asc">Sort: Status (A-Z)</option>
              <option value="priority-desc">Sort: Priority (Tinggi)</option>
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Dari Tanggal</label>
            <Input
              type="date"
              value={filter.date_from}
              onChange={(e) => setFilter(prev => ({ ...prev, date_from: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sampai Tanggal</label>
            <Input
              type="date"
              value={filter.date_to}
              onChange={(e) => setFilter(prev => ({ ...prev, date_to: e.target.value }))}
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-800">
              Task List ({filteredAndSortedTasks.length})
            </h2>
          </div>
        </div>
        <Table
          data={filteredAndSortedTasks}
          columns={columns}
          loading={isLoading}
          emptyMessage="Tidak ada task ditemukan"
        />
      </div>
    </div>
  );
};

export default EnhancedNotionTasksPage;

