/**
 * Mobil Calendar Page
 * Calendar view untuk reservasi mobil dengan Tailwind CSS
 */

import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useGetMobilCalendarQuery, useGetMobilsQuery } from '../store';
import { Button } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import Swal from 'sweetalert2';

const MobilCalendarPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const month = currentMonth.getMonth() + 1;
  const year = currentMonth.getFullYear();
  const hasOpenedModalRef = useRef(false);

  // Auto-refresh setiap 60 detik
  const { data: calendarData, isLoading, refetch } = useGetMobilCalendarQuery(
    { month, year },
    {
      pollingInterval: 60000, // 60 detik
      refetchOnMountOrArgChange: true,
    }
  );
  const { data: mobilsData, refetch: refetchMobils } = useGetMobilsQuery(
    { page: 1, per_page: 100 },
    {
      pollingInterval: 60000, // 60 detik
    }
  );

  // Refetch saat bulan berubah
  useEffect(() => {
    refetch();
    refetchMobils();
  }, [month, year, refetch, refetchMobils]);

  const mobils = mobilsData?.items || [];
  const calendar = calendarData || {};

  // Auto-open modal setelah create request berhasil
  useEffect(() => {
    const openModal = searchParams.get('open_modal');
    const mobilId = searchParams.get('mobil_id');
    const dateStr = searchParams.get('date');
    
    if (openModal === 'true' && mobilId && dateStr && !hasOpenedModalRef.current) {
      hasOpenedModalRef.current = true;
      
      // Refresh data dulu, lalu open modal
      const refreshAndOpenModal = async () => {
        try {
          // Refetch data
          const calendarResult = await refetch();
          await refetchMobils();
          
          // Tunggu sebentar untuk memastikan state ter-update
          setTimeout(() => {
            // Parse date
            const date = new Date(dateStr);
            const dateStrFormatted = formatDate(date);
            
            // Get fresh data dari result atau dari calendarData yang sudah ter-update
            const freshCalendarData = calendarResult.data || calendarData || {};
            const freshMobils = mobilsData?.items || mobils || [];
            
            const mobil = freshMobils.find(m => m.id === parseInt(mobilId));
            if (mobil) {
              // Get reservations dari fresh data
              const mobilData = freshCalendarData[mobil.id];
              const updatedReservations = mobilData?.[dateStrFormatted] || [];
              showReservationDetails(updatedReservations, mobil, date);
            }
            
            // Clean URL dan reset flag
            setSearchParams({});
            hasOpenedModalRef.current = false;
          }, 1000);
        } catch (error) {
          console.error('Error refreshing data:', error);
          hasOpenedModalRef.current = false;
        }
      };
      
      refreshAndOpenModal();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newMonth = new Date(currentMonth);
    if (direction === 'prev') {
      newMonth.setMonth(newMonth.getMonth() - 1);
    } else {
      newMonth.setMonth(newMonth.getMonth() + 1);
    }
    setCurrentMonth(newMonth);
  };

  const getDaysInMonth = () => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days = [];
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day));
    }
    return days;
  };

  const formatDate = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const getReservationsForDate = (mobilId: number, date: Date) => {
    const dateStr = formatDate(date);
    const mobilData = calendar[mobilId];
    if (!mobilData) return [];
    return mobilData[dateStr] || [];
  };

  const formatDateTime = (dateStr: string, timeStr?: string) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    const day = String(date.getDate()).padStart(2, '0');
    const month = monthNames[date.getMonth()];
    const year = date.getFullYear();
    const time = timeStr ? ` ${timeStr.substring(0, 5)}` : '';
    return `${day} ${month} ${year}${time}`;
  };

  const getStatusBadge = (status: string) => {
    const statusLower = status?.toLowerCase() || 'unknown';
    if (statusLower === 'active') {
      return '<span class="px-2 py-1 rounded text-xs font-semibold bg-green-100 text-green-800">Aktif</span>';
    } else if (statusLower === 'cancelled' || statusLower === 'canceled') {
      return '<span class="px-2 py-1 rounded text-xs font-semibold bg-gray-200 text-gray-600 line-through">Dibatalkan</span>';
    } else if (statusLower === 'pending' || statusLower === 'waiting') {
      return '<span class="px-2 py-1 rounded text-xs font-semibold bg-yellow-100 text-yellow-800">Pending</span>';
    }
    return '<span class="px-2 py-1 rounded text-xs font-semibold bg-blue-100 text-blue-800">' + status + '</span>';
  };

  const showReservationDetails = (reservations: any[], mobil: any, date: Date) => {
    if (!reservations || reservations.length === 0) return;

    const dateStr = formatDate(date);
    const dateFormatted = formatDateTime(dateStr);

    let htmlContent = `
      <div class="text-left space-y-4">
        <div class="border-b pb-2 mb-3">
          <h3 class="text-lg font-semibold text-gray-800">📅 Detail Reservasi</h3>
          <p class="text-sm text-gray-600 mt-1">${dateFormatted}</p>
          <p class="text-sm text-gray-600">Mobil: <strong>${mobil.nama || mobil.nama_mobil}</strong> (${mobil.plat_nomor})</p>
        </div>
    `;

    if (reservations.length === 1) {
      const res = reservations[0];
      htmlContent += `
        <div class="space-y-3">
          <div class="bg-gray-50 p-3 rounded-lg">
            <div class="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span class="font-semibold text-gray-700">👤 User:</span>
                <p class="text-gray-800 mt-1">${res.user?.username || 'Tidak diketahui'}</p>
                ${res.user?.email ? `<p class="text-xs text-gray-500">${res.user.email}</p>` : ''}
                ${res.user?.role ? `<p class="text-xs text-gray-500">Role: ${res.user.role}</p>` : ''}
              </div>
              <div>
                <span class="font-semibold text-gray-700">📊 Status:</span>
                <p class="mt-1">${getStatusBadge(res.status || 'unknown')}</p>
              </div>
            </div>
          </div>
          
          <div class="bg-gray-50 p-3 rounded-lg">
            <div class="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span class="font-semibold text-gray-700">📅 Tanggal Mulai:</span>
                <p class="text-gray-800 mt-1">${formatDateTime(res.tanggal_mulai || res.start_date)}</p>
              </div>
              <div>
                <span class="font-semibold text-gray-700">📅 Tanggal Selesai:</span>
                <p class="text-gray-800 mt-1">${formatDateTime(res.tanggal_selesai || res.end_date)}</p>
              </div>
            </div>
          </div>
          
          ${res.jam_mulai && res.jam_selesai ? `
          <div class="bg-gray-50 p-3 rounded-lg">
            <div class="text-sm">
              <span class="font-semibold text-gray-700">🕐 Jam:</span>
              <p class="text-gray-800 mt-1">${res.jam_mulai.substring(0, 5)} - ${res.jam_selesai.substring(0, 5)}</p>
            </div>
          </div>
          ` : ''}
          
          ${res.keperluan || res.purpose ? `
          <div class="bg-gray-50 p-3 rounded-lg">
            <div class="text-sm">
              <span class="font-semibold text-gray-700">📝 Keperluan:</span>
              <p class="text-gray-800 mt-1">${res.keperluan || res.purpose}</p>
            </div>
          </div>
          ` : ''}
          
          ${res.is_recurring ? `
          <div class="bg-blue-50 p-3 rounded-lg border border-blue-200">
            <div class="text-sm">
              <span class="font-semibold text-blue-700">🔄 Reservasi Berulang:</span>
              <p class="text-blue-800 mt-1">Ya</p>
              ${res.recurring_pattern ? `<p class="text-xs text-blue-600 mt-1">Pola: ${res.recurring_pattern}</p>` : ''}
              ${res.recurring_end_date ? `<p class="text-xs text-blue-600 mt-1">Berakhir: ${formatDateTime(res.recurring_end_date)}</p>` : ''}
            </div>
          </div>
          ` : ''}
          
          ${res.is_backup_mobil ? `
          <div class="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
            <div class="text-sm">
              <span class="font-semibold text-yellow-700">⚠️ Mobil Backup:</span>
              <p class="text-yellow-800 mt-1">Reservasi ini menggunakan mobil backup</p>
            </div>
          </div>
          ` : ''}
          
          ${res.created_at ? `
          <div class="text-xs text-gray-500 pt-2 border-t">
            <p>Dibuat: ${formatDateTime(res.created_at)}</p>
            ${res.updated_at ? `<p>Diperbarui: ${formatDateTime(res.updated_at)}</p>` : ''}
          </div>
          ` : ''}
        </div>
      `;
    } else {
      htmlContent += `
        <div class="space-y-3">
          <p class="text-sm text-gray-600 mb-3">Terdapat <strong>${reservations.length}</strong> reservasi pada tanggal ini:</p>
      `;
      
      reservations.forEach((res, index) => {
        htmlContent += `
          <div class="bg-gray-50 p-3 rounded-lg border border-gray-200">
            <div class="flex justify-between items-start mb-2">
              <h4 class="font-semibold text-gray-800">Reservasi #${index + 1}</h4>
              ${getStatusBadge(res.status || 'unknown')}
            </div>
            <div class="grid grid-cols-2 gap-2 text-sm mt-2">
              <div>
                <span class="font-semibold text-gray-700">👤 User:</span>
                <p class="text-gray-800">${res.user?.username || 'Tidak diketahui'}</p>
              </div>
              <div>
                <span class="font-semibold text-gray-700">🕐 Jam:</span>
                <p class="text-gray-800">${res.jam_mulai ? res.jam_mulai.substring(0, 5) : '-'} - ${res.jam_selesai ? res.jam_selesai.substring(0, 5) : '-'}</p>
              </div>
            </div>
            ${res.keperluan || res.purpose ? `
            <div class="mt-2 text-sm">
              <span class="font-semibold text-gray-700">📝 Keperluan:</span>
              <p class="text-gray-800">${res.keperluan || res.purpose}</p>
            </div>
            ` : ''}
            <div class="mt-2 text-xs text-gray-500">
              <p>Tanggal: ${formatDateTime(res.tanggal_mulai || res.start_date)} - ${formatDateTime(res.tanggal_selesai || res.end_date)}</p>
            </div>
          </div>
        `;
      });
      
      htmlContent += `</div>`;
    }

    htmlContent += `</div>`;

    Swal.fire({
      title: 'Detail Reservasi',
      html: htmlContent,
      width: '600px',
      showCancelButton: true,
      confirmButtonText: 'Tutup',
      cancelButtonText: 'Request Mobil',
      confirmButtonColor: '#3085d6',
      cancelButtonColor: '#28a745',
      customClass: {
        popup: 'text-left',
        htmlContainer: 'text-left'
      }
    }).then((result) => {
      if (result.dismiss === Swal.DismissReason.cancel) {
        // Navigate ke request page dengan data pre-filled
        const dateStr = formatDate(date);
        navigate(`/mobil/request?tanggal_mulai=${dateStr}&tanggal_selesai=${dateStr}&mobil_id=${mobil.id}`);
      }
    });
  };

  const monthNames = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
  ];

  const dayNames = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];

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
            <h1 className="text-2xl md:text-3xl font-bold text-gray-800 mb-2">📅 Kalender Reservasi Mobil</h1>
            <p className="text-gray-600">
              {monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigateMonth('prev')}>
              ← Bulan Sebelumnya
            </Button>
            <Button variant="outline" onClick={() => navigateMonth('next')}>
              Bulan Selanjutnya →
            </Button>
            <Link to="/mobil/dashboard">
              <Button variant="outline">← Kembali</Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Calendar */}
      <div className="bg-white rounded-lg shadow-md p-6 overflow-x-auto">
        <div className="min-w-full">
          {/* Day Headers */}
          <div className="grid grid-cols-8 gap-2 mb-4">
            <div className="font-semibold text-gray-700">Mobil</div>
            {dayNames.map(day => (
              <div key={day} className="text-center font-semibold text-gray-700 text-sm">
                {day.substring(0, 3)}
              </div>
            ))}
          </div>

          {/* Calendar Grid */}
          <div className="space-y-2">
            {mobils.map(mobil => {
              const days = getDaysInMonth();
              return (
                <div key={mobil.id} className="grid grid-cols-8 gap-2 items-start">
                  <div className="font-medium text-sm p-2 border-r border-gray-200">
                    <div>{mobil.nama || mobil.nama_mobil}</div>
                    <div className="text-xs text-gray-500">{mobil.plat_nomor}</div>
                  </div>
                  {days.map((date, index) => {
                    if (!date) {
                      return <div key={index} className="p-2"></div>;
                    }
                    const reservations = getReservationsForDate(mobil.id, date);
                    const isToday = formatDate(date) === formatDate(new Date());
                    const hasReservations = reservations.length > 0;
                    
                    const handleDateClick = () => {
                      if (hasReservations) {
                        // Jika ada reservasi, tampilkan modal detail
                        showReservationDetails(reservations, mobil, date);
                      } else {
                        // Jika tidak ada reservasi, navigate ke halaman request dengan tanggal terisi
                        const dateStr = formatDate(date);
                        const nextDay = new Date(date);
                        nextDay.setDate(nextDay.getDate() + 1);
                        const nextDayStr = formatDate(nextDay);
                        
                        // Navigate dengan query params
                        navigate(`/mobil/request?tanggal_mulai=${dateStr}&tanggal_selesai=${nextDayStr}&mobil_id=${mobil.id}`);
                      }
                    };
                    
                    return (
                      <div
                        key={index}
                        className={`p-2 min-h-[60px] border border-gray-200 rounded ${
                          isToday ? 'bg-blue-50 border-blue-300' : ''
                        } cursor-pointer hover:bg-gray-50 transition-colors`}
                        onClick={handleDateClick}
                        title={hasReservations ? 'Klik untuk melihat detail reservasi' : 'Klik untuk membuat request mobil'}
                      >
                        <div className="text-xs font-medium mb-1">{date.getDate()}</div>
                        {reservations.length > 0 && (
                          <div className="space-y-1">
                            {reservations.slice(0, 3).map((res: any, idx: number) => {
                              // Tentukan warna berdasarkan status
                              const status = res.status?.toLowerCase() || 'unknown';
                              let statusColor = 'bg-primary-100 text-primary-800'; // default untuk active
                              
                              if (status === 'cancelled' || status === 'canceled') {
                                statusColor = 'bg-gray-200 text-gray-600 line-through';
                              } else if (status === 'pending' || status === 'waiting') {
                                statusColor = 'bg-yellow-100 text-yellow-800';
                              } else if (status === 'active') {
                                statusColor = 'bg-primary-100 text-primary-800';
                              } else {
                                statusColor = 'bg-blue-100 text-blue-800';
                              }
                              
                              const tooltipText = `Klik untuk melihat detail\n${res.user?.username || 'User'} - ${res.keperluan || res.purpose || 'Tidak ada keperluan'} (Status: ${res.status || 'unknown'})${res.jam_mulai && res.jam_selesai ? ` | ${res.jam_mulai.substring(0, 5)} - ${res.jam_selesai.substring(0, 5)}` : ''}`;
                              
                              return (
                                <div
                                  key={res.id || idx}
                                  className={`text-xs ${statusColor} rounded px-1 py-0.5 truncate cursor-pointer hover:opacity-80 transition-opacity`}
                                  title={tooltipText}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    showReservationDetails([res], mobil, date);
                                  }}
                                >
                                  {res.user?.username || 'User'}
                                </div>
                              );
                            })}
                            {reservations.length > 3 && (
                              <div 
                                className="text-xs text-gray-500 font-semibold cursor-pointer hover:text-gray-700"
                                title="Klik untuk melihat semua reservasi"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  showReservationDetails(reservations, mobil, date);
                                }}
                              >
                                +{reservations.length - 3} lagi
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-white rounded-lg shadow-md p-4 mt-6">
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-50 border border-blue-300 rounded"></div>
            <span>Hari Ini</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-primary-100 rounded"></div>
            <span>Reservasi Aktif</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gray-200 rounded line-through"></div>
            <span>Reservasi Dibatalkan</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-100 rounded"></div>
            <span>Reservasi Pending</span>
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <span className="text-xs text-gray-500">
              🔄 Auto-refresh setiap 60 detik
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MobilCalendarPage;

