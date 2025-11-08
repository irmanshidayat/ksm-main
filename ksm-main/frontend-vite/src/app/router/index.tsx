/**
 * Main Router Component
 * Router configuration dengan React Router v6
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './guards/ProtectedRoute';
import { LoginPage } from '@/features/auth';
import { DashboardPage } from '@/features/dashboard';
import { 
  DashboardStokPage, 
  BarangMasukPage, 
  BarangKeluarPage,
  TambahKategoriPage,
  CategoryListPage,
  TambahBarangPage,
  StokBarangListPage,
  DaftarBarangMasukPage
} from '@/features/stok-barang';
import { 
  VendorDashboardPage,
  VendorProfilePage,
  VendorRequestsPage,
  VendorRequestDetailPage,
  VendorUploadPenawaranPage,
  VendorHistoryPage,
  VendorPesananPage,
  VendorPesananDetailPage,
  VendorTemplatesPage,
  VendorNotificationsPage,
  VendorListPage,
  VendorDetailPage,
  VendorSelfRegistrationPage
} from '@/features/vendor-management';
import { 
  RequestPembelianDashboardPage,
  RequestPembelianListPage,
  RequestPembelianDetailPage,
  RequestPembelianFormPage,
  VendorAnalysisDashboardPage,
  UploadPenawaranSelectorPage,
  VendorPenawaranUploadPage,
  VendorPenawaranApprovalPage,
  DaftarBarangVendorPage,
  EmailComposerPage,
  BulkVendorImportPage,
  GmailCallbackPage,
  LaporanPembelianPage
} from '@/features/request-pembelian';
import { 
  MobilDashboardPage,
  MobilAddPage,
  MobilHistoryPage,
  MobilCalendarPage,
  MobilRequestPage
} from '@/features/mobil-management';
import {
  AttendanceDashboardPage,
  AttendanceClockInPage,
  AttendanceHistoryPage,
  LeaveRequestPage,
  AttendanceReportPage,
  DailyTaskPage,
  TaskDashboardPage
} from '@/features/attendance-management';
import { UserManagementPage } from '@/features/user-management';
import { RoleManagementPage } from '@/features/role-management';
import { NotificationsPage } from '@/features/notifications';
import { ApprovalManagementPage } from '@/features/approval-management';
import { TelegramBotManagementPage } from '@/features/telegram-bot';
import { AgentStatusPage } from '@/features/agent-status';
import { RemindExpDocsPage } from '@/features/remind-exp-docs';
import { EnhancedNotionTasksPage } from '@/features/enhanced-notion-tasks';
import { DatabaseDiscoveryPage } from '@/features/database-discovery';
import { EnhancedDatabasePage } from '@/features/enhanced-database';
import { QdrantKnowledgeBasePage } from '@/features/qdrant-knowledge-base';
import { KnowledgeAIPage } from '@/features/knowledge-ai';
import { PermissionManagementPage, PermissionOverviewPage, PermissionMatrixPage, LevelPermissionMatrixPage } from '@/features/permission-management';

const AppRouter: React.FC = () => {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/vendor/register" element={<VendorSelfRegistrationPage />} />
        <Route path="/request-pembelian/auth/gmail/callback" element={<GmailCallbackPage />} />
        
        {/* Root redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* Protected Routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        
        {/* Vendor Management Routes */}
        <Route
          path="/vendor/dashboard"
          element={
            <ProtectedRoute>
              <VendorDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vendor/profile"
          element={
            <ProtectedRoute>
              <VendorProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vendor/requests"
          element={
            <ProtectedRoute>
              <VendorRequestsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vendor/requests/:requestId"
          element={
            <ProtectedRoute>
              <VendorRequestDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vendor/upload-penawaran/:requestId"
          element={
            <ProtectedRoute>
              <VendorUploadPenawaranPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vendor/history"
          element={
            <ProtectedRoute>
              <VendorHistoryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vendor/pesanan"
          element={
            <ProtectedRoute>
              <VendorPesananPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vendor/templates"
          element={
            <ProtectedRoute>
              <VendorTemplatesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vendor/notifications"
          element={
            <ProtectedRoute>
              <VendorNotificationsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vendor/pesanan/:orderId"
          element={
            <ProtectedRoute>
              <VendorPesananDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vendor/daftar"
          element={
            <ProtectedRoute>
              <VendorListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vendor/detail/:id"
          element={
            <ProtectedRoute>
              <VendorDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/vendor/*"
          element={
            <ProtectedRoute>
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <h1 className="text-2xl font-bold mb-4">Vendor Feature</h1>
                  <p className="text-text-secondary">Feature akan diimplementasikan</p>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
        {/* Request Pembelian Routes */}
        <Route
          path="/request-pembelian"
          element={
            <ProtectedRoute>
              <RequestPembelianDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/dashboard"
          element={
            <ProtectedRoute>
              <RequestPembelianDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/daftar-request"
          element={
            <ProtectedRoute>
              <RequestPembelianListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/detail/:id"
          element={
            <ProtectedRoute>
              <RequestPembelianDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/buat-request"
          element={
            <ProtectedRoute>
              <RequestPembelianFormPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/edit-request/:id"
          element={
            <ProtectedRoute>
              <RequestPembelianFormPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/upload-penawaran"
          element={
            <ProtectedRoute>
              <UploadPenawaranSelectorPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/analisis-vendor"
          element={
            <ProtectedRoute>
              <VendorAnalysisDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/analisis-vendor/:requestId"
          element={
            <ProtectedRoute>
              <VendorAnalysisDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/upload-penawaran/:vendorId/:requestId"
          element={
            <ProtectedRoute>
              <VendorPenawaranUploadPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/vendor-penawaran"
          element={
            <ProtectedRoute>
              <VendorPenawaranApprovalPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/daftar-barang-vendor"
          element={
            <ProtectedRoute>
              <DaftarBarangVendorPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/email-composer"
          element={
            <ProtectedRoute>
              <EmailComposerPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/bulk-import"
          element={
            <ProtectedRoute>
              <BulkVendorImportPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/laporan-pembelian"
          element={
            <ProtectedRoute>
              <LaporanPembelianPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/request-pembelian/*"
          element={
            <ProtectedRoute>
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <h1 className="text-2xl font-bold mb-4">Request Pembelian</h1>
                  <p className="text-text-secondary">Feature akan diimplementasikan</p>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
        {/* Mobil Management Routes */}
        <Route
          path="/mobil"
          element={
            <ProtectedRoute>
              <MobilDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/mobil/dashboard"
          element={
            <ProtectedRoute>
              <MobilDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/mobil/calendar"
          element={
            <ProtectedRoute>
              <MobilCalendarPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/mobil/request"
          element={
            <ProtectedRoute>
              <MobilRequestPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/mobil/add"
          element={
            <ProtectedRoute>
              <MobilAddPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/mobil/history"
          element={
            <ProtectedRoute>
              <MobilHistoryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/mobil/*"
          element={
            <ProtectedRoute>
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <h1 className="text-2xl font-bold mb-4">Mobil Management</h1>
                  <p className="text-text-secondary">Feature akan diimplementasikan</p>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
        {/* Attendance Management Routes */}
        <Route
          path="/attendance"
          element={
            <ProtectedRoute>
              <AttendanceDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/attendance/dashboard"
          element={
            <ProtectedRoute>
              <AttendanceDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/attendance/clock-in"
          element={
            <ProtectedRoute>
              <AttendanceClockInPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/attendance/history"
          element={
            <ProtectedRoute>
              <AttendanceHistoryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/attendance/leave-request"
          element={
            <ProtectedRoute>
              <LeaveRequestPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/attendance/report"
          element={
            <ProtectedRoute>
              <AttendanceReportPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/attendance/daily-task"
          element={
            <ProtectedRoute>
              <DailyTaskPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/attendance/task-dashboard"
          element={
            <ProtectedRoute>
              <TaskDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/attendance/*"
          element={
            <ProtectedRoute>
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <h1 className="text-2xl font-bold mb-4">Attendance Management</h1>
                  <p className="text-text-secondary">Feature akan diimplementasikan</p>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
        {/* User Management Routes */}
        <Route
          path="/users"
          element={
            <ProtectedRoute>
              <UserManagementPage />
            </ProtectedRoute>
          }
        />
        {/* Role Management Routes */}
        <Route
          path="/roles"
          element={
            <ProtectedRoute>
              <RoleManagementPage />
            </ProtectedRoute>
          }
        />
        {/* Notifications Routes */}
        <Route
          path="/notifications"
          element={
            <ProtectedRoute>
              <NotificationsPage />
            </ProtectedRoute>
          }
        />
        {/* Approval Management Routes */}
        <Route
          path="/approval-management"
          element={
            <ProtectedRoute>
              <ApprovalManagementPage />
            </ProtectedRoute>
          }
        />
        {/* Telegram Bot Management Routes */}
        <Route
          path="/telegram-bot"
          element={
            <ProtectedRoute>
              <TelegramBotManagementPage />
            </ProtectedRoute>
          }
        />
        {/* Agent Status Routes */}
        <Route
          path="/agent-status"
          element={
            <ProtectedRoute>
              <AgentStatusPage />
            </ProtectedRoute>
          }
        />
        {/* Remind Exp Docs Routes */}
        <Route
          path="/remind-exp-docs"
          element={
            <ProtectedRoute>
              <RemindExpDocsPage />
            </ProtectedRoute>
          }
        />
        {/* Enhanced Notion Tasks Routes */}
        <Route
          path="/enhanced-notion-tasks"
          element={
            <ProtectedRoute>
              <EnhancedNotionTasksPage />
            </ProtectedRoute>
          }
        />
        {/* Database Discovery Routes */}
        <Route
          path="/database-discovery"
          element={
            <ProtectedRoute>
              <DatabaseDiscoveryPage />
            </ProtectedRoute>
          }
        />
        {/* Enhanced Database Routes */}
        <Route
          path="/enhanced-database"
          element={
            <ProtectedRoute>
              <EnhancedDatabasePage />
            </ProtectedRoute>
          }
        />
        {/* Qdrant Knowledge Base Routes */}
        <Route
          path="/qdrant-knowledge-base"
          element={
            <ProtectedRoute>
              <QdrantKnowledgeBasePage />
            </ProtectedRoute>
          }
        />
        {/* Knowledge AI Routes */}
        <Route
          path="/ksm-ai"
          element={
            <ProtectedRoute>
              <KnowledgeAIPage />
            </ProtectedRoute>
          }
        />
        {/* Permission Management Routes */}
        <Route
          path="/permissions"
          element={
            <ProtectedRoute>
              <PermissionManagementPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/permissions/overview"
          element={
            <ProtectedRoute>
              <PermissionOverviewPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/roles/:roleId/permissions"
          element={
            <ProtectedRoute>
              <PermissionMatrixPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/roles/level-permissions"
          element={
            <ProtectedRoute>
              <LevelPermissionMatrixPage />
            </ProtectedRoute>
          }
        />
        {/* Stok Barang Routes */}
        <Route
          path="/stok-barang"
          element={
            <ProtectedRoute>
              <DashboardStokPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/stok-barang/dashboard"
          element={
            <ProtectedRoute>
              <DashboardStokPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/stok-barang/barang-masuk"
          element={
            <ProtectedRoute>
              <BarangMasukPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/stok-barang/barang-keluar"
          element={
            <ProtectedRoute>
              <BarangKeluarPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/stok-barang/tambah-kategori"
          element={
            <ProtectedRoute>
              <TambahKategoriPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/stok-barang/category"
          element={
            <ProtectedRoute>
              <CategoryListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/stok-barang/daftar-barang"
          element={
            <ProtectedRoute>
              <StokBarangListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/stok-barang/tambah-barang"
          element={
            <ProtectedRoute>
              <TambahBarangPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/stok-barang/daftar-barang-masuk"
          element={
            <ProtectedRoute>
              <DaftarBarangMasukPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/stok-barang/*"
          element={
            <ProtectedRoute>
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <h1 className="text-2xl font-bold mb-4">Stok Barang</h1>
                  <p className="text-text-secondary">Halaman sedang dalam pengembangan</p>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
        <Route
          path="/mobil/*"
          element={
            <ProtectedRoute>
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <h1 className="text-2xl font-bold mb-4">Mobil</h1>
                  <p className="text-text-secondary">Feature akan diimplementasikan</p>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
        <Route
          path="/attendance/*"
          element={
            <ProtectedRoute>
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <h1 className="text-2xl font-bold mb-4">Attendance</h1>
                  <p className="text-text-secondary">Feature akan diimplementasikan</p>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
        <Route
          path="/notifications"
          element={
            <ProtectedRoute>
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <h1 className="text-2xl font-bold mb-4">Notifications</h1>
                  <p className="text-text-secondary">Feature akan diimplementasikan</p>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
        <Route
          path="/user-management"
          element={
            <ProtectedRoute>
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <h1 className="text-2xl font-bold mb-4">User Management</h1>
                  <p className="text-text-secondary">Feature akan diimplementasikan</p>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
        <Route
          path="/role-management"
          element={
            <ProtectedRoute>
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <h1 className="text-2xl font-bold mb-4">Role Management</h1>
                  <p className="text-text-secondary">Feature akan diimplementasikan</p>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
        <Route
          path="/permission-management"
          element={
            <ProtectedRoute>
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <h1 className="text-2xl font-bold mb-4">Permission Management</h1>
                  <p className="text-text-secondary">Feature akan diimplementasikan</p>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
        
        {/* Catch all - redirect to dashboard */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default AppRouter;

