/**
 * Attendance Clock In Page
 * Halaman untuk clock in/out dengan kamera dan lokasi GPS otomatis
 * Menggunakan Tailwind CSS untuk styling responsif
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetTodayStatusQuery, useGetAttendancesQuery, useClockInMutation, useClockOutMutation } from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import { Camera, MapPin, RefreshCw, X, CheckCircle, AlertCircle } from 'lucide-react';

const AttendanceClockInPage: React.FC = () => {
  const navigate = useNavigate();
  const sweetAlert = useSweetAlert();
  const { data: todayStatus, isLoading: loadingStatus, refetch: refetchStatus } = useGetTodayStatusQuery();
  const { data: todayAttendance } = useGetAttendancesQuery({
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    per_page: 1,
  });
  const [clockIn, { isLoading: clockingIn }] = useClockInMutation();
  const [clockOut, { isLoading: clockingOut }] = useClockOutMutation();

  // Location state
  const [location, setLocation] = useState<{ lat: number | null; lng: number | null; address: string }>({
    lat: null,
    lng: null,
    address: '',
  });
  const [locationLoading, setLocationLoading] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);

  // Camera state
  const [cameraOpen, setCameraOpen] = useState(false);
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Form state
  const [notes, setNotes] = useState('');

  // Reverse geocoding function
  const reverseGeocode = async (lat: number, lng: number): Promise<string> => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`,
        {
          headers: {
            'User-Agent': 'KSM-Attendance-App/1.0'
          }
        }
      );

      if (!response.ok) {
        throw new Error('Reverse geocoding failed');
      }

      const data = await response.json();
      
      if (data.display_name) {
        return data.display_name;
      } else {
        return `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
      }
    } catch (error) {
      // Fallback ke koordinat jika reverse geocoding gagal
      return `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    }
  };

  // Get current location automatically on mount
  useEffect(() => {
    getCurrentLocation();
  }, []);

  // Set video stream to video element when camera opens
  useEffect(() => {
    if (cameraOpen && cameraStream && videoRef.current) {
      videoRef.current.srcObject = cameraStream;
      videoRef.current.play().catch(error => {
        console.error('Error playing video:', error);
      });
    }
  }, [cameraOpen, cameraStream]);

  // Cleanup camera stream on unmount
  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [cameraStream]);

  const getCurrentLocation = async () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation tidak didukung di browser ini');
      await sweetAlert.showError('Error', 'Geolocation tidak didukung di browser ini');
      return;
    }

    try {
      setLocationLoading(true);
      setLocationError(null);
      sweetAlert.showLoading('Mengambil Lokasi', 'Sedang mengambil lokasi GPS...');

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          
          // Get address via reverse geocoding
          const address = await reverseGeocode(lat, lng);
          
          setLocation({ lat, lng, address });
          setLocationLoading(false);
          sweetAlert.hideLoading();
          await sweetAlert.showSuccessAuto('Lokasi Berhasil Diambil', 'Lokasi GPS berhasil diperoleh', 1500);
        },
        async (error) => {
          setLocationLoading(false);
          sweetAlert.hideLoading();
          
          let errorMessage = 'Gagal mendapatkan lokasi';
          switch (error.code) {
            case error.PERMISSION_DENIED:
              errorMessage = 'Izin lokasi ditolak. Silakan aktifkan izin lokasi di pengaturan browser.';
              break;
            case error.POSITION_UNAVAILABLE:
              errorMessage = 'Informasi lokasi tidak tersedia.';
              break;
            case error.TIMEOUT:
              errorMessage = 'Waktu permintaan lokasi habis.';
              break;
          }
          
          setLocationError(errorMessage);
          await sweetAlert.showError('Gagal Mengambil Lokasi', errorMessage);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    } catch (error) {
      setLocationLoading(false);
      sweetAlert.hideLoading();
      const errorMessage = error instanceof Error ? error.message : 'Terjadi kesalahan saat mengambil lokasi';
      setLocationError(errorMessage);
      await sweetAlert.showError('Error', errorMessage);
    }
  };

  const openCamera = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Kamera tidak didukung di browser ini');
      }

      sweetAlert.showLoading('Membuka Kamera', 'Sedang mengakses kamera...');

      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'user', // Front camera
          width: { ideal: 1280 },
          height: { ideal: 720 }
        } 
      });

      setCameraStream(stream);
      setCameraOpen(true);
      
      // Set video source and play
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(error => {
          console.error('Error playing video:', error);
        });
      }

      sweetAlert.hideLoading();
    } catch (error) {
      sweetAlert.hideLoading();
      const errorMessage = error instanceof Error ? error.message : 'Tidak dapat mengakses kamera. Pastikan izin kamera sudah diberikan.';
      await sweetAlert.showError('Gagal Membuka Kamera', errorMessage);
      console.error('Error accessing camera:', error);
    }
  };

  const closeCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
      setCameraStream(null);
    }
    setCameraOpen(false);
  };

  const capturePhoto = async () => {
    try {
      if (!videoRef.current || !canvasRef.current) {
        throw new Error('Video atau canvas tidak tersedia');
      }

      sweetAlert.showLoading('Mengambil Foto', 'Sedang mengambil foto...');

      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      if (!context) {
        throw new Error('Canvas context tidak tersedia');
      }

      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      
      // Mirror the image untuk selfie (seperti preview)
      context.translate(canvas.width, 0);
      context.scale(-1, 1);
      context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      
      // Reset transform
      context.setTransform(1, 0, 0, 1, 0, 0);
      
      const photoDataUrl = canvas.toDataURL('image/jpeg', 0.8);
      setCapturedPhoto(photoDataUrl);
      closeCamera();
      
      sweetAlert.hideLoading();
      await sweetAlert.showSuccessAuto('Foto Berhasil Diambil', 'Foto selfie berhasil diambil', 1500);
    } catch (error) {
      sweetAlert.hideLoading();
      const errorMessage = error instanceof Error ? error.message : 'Gagal mengambil foto';
      await sweetAlert.showError('Gagal Mengambil Foto', errorMessage);
      console.error('Error capturing photo:', error);
    }
  };

  const handleClockIn = async () => {
    if (!location.lat || !location.lng) {
      await sweetAlert.showError('Lokasi GPS Wajib', 'Lokasi GPS wajib diisi sebelum clock in. Silakan ambil lokasi terlebih dahulu.');
      return;
    }

    if (!capturedPhoto) {
      await sweetAlert.showError('Foto Wajib', 'Foto selfie wajib diambil sebelum clock in. Silakan ambil foto terlebih dahulu.');
      return;
    }

    try {
      sweetAlert.showLoading('Clock In', 'Sedang melakukan clock in...');

      await clockIn({
        latitude: location.lat!,
        longitude: location.lng!,
        address: location.address,
        photo: capturedPhoto,
        notes: notes.trim(),
      }).unwrap();

      sweetAlert.hideLoading();
      await sweetAlert.showSuccessAuto('Clock In Berhasil', 'Clock in berhasil dilakukan');
      setCapturedPhoto(null);
      setNotes('');
      refetchStatus();
    } catch (error: any) {
      sweetAlert.hideLoading();
      await sweetAlert.showError('Gagal Clock In', error?.data?.message || error?.message || 'Gagal melakukan clock in');
    }
  };

  const handleClockOut = async () => {
    if (!todayStatus?.has_clocked_in) {
      await sweetAlert.showError('Error', 'Anda belum melakukan clock in hari ini');
      return;
    }

    if (!location.lat || !location.lng) {
      await sweetAlert.showError('Lokasi GPS Wajib', 'Lokasi GPS wajib diisi sebelum clock out. Silakan ambil lokasi terlebih dahulu.');
      return;
    }

    if (!capturedPhoto) {
      await sweetAlert.showError('Foto Wajib', 'Foto selfie wajib diambil sebelum clock out. Silakan ambil foto terlebih dahulu.');
      return;
    }

    try {
      // Get today's attendance record ID
      const todayRecord = todayAttendance?.items?.[0];
      if (!todayRecord) {
        await sweetAlert.showError('Error', 'Tidak dapat menemukan record absensi hari ini');
        return;
      }

      sweetAlert.showLoading('Clock Out', 'Sedang melakukan clock out...');

      await clockOut({
        attendance_id: todayRecord.id,
        latitude: location.lat!,
        longitude: location.lng!,
        address: location.address,
        photo: capturedPhoto,
        notes: notes.trim(),
      }).unwrap();

      sweetAlert.hideLoading();
      await sweetAlert.showSuccessAuto('Clock Out Berhasil', 'Clock out berhasil dilakukan');
      setCapturedPhoto(null);
      setNotes('');
      refetchStatus();
    } catch (error: any) {
      sweetAlert.hideLoading();
      await sweetAlert.showError('Gagal Clock Out', error?.data?.message || error?.message || 'Gagal melakukan clock out');
    }
  };

  if (loadingStatus) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  const canClockIn = todayStatus && !todayStatus.has_clocked_in;
  const canClockOut = todayStatus && todayStatus.has_clocked_in && !todayStatus.has_clocked_out;

  return (
    <div className="p-4 md:p-6 lg:p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6 mb-4 md:mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-xl md:text-2xl lg:text-3xl font-bold text-gray-800 mb-2 flex items-center gap-2">
              <span>⏰</span>
              <span>Absensi Karyawan</span>
            </h1>
            <p className="text-sm md:text-base text-gray-600">Lakukan clock in/out dengan foto dan lokasi GPS</p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate('/attendance/dashboard')}
            className="w-full md:w-auto"
          >
            ← Kembali
          </Button>
        </div>
      </div>

      {/* Status Card */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6 mb-4 md:mb-6">
        <h2 className="text-lg md:text-xl font-semibold text-gray-800 mb-4">Status Hari Ini</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-2">Clock In</div>
            <div className="text-xl md:text-2xl font-bold text-gray-800 flex items-center gap-2">
              {todayStatus?.has_clocked_in ? (
                <>
                  <CheckCircle className="w-6 h-6 text-green-500" />
                  <span>Sudah</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-6 h-6 text-red-500" />
                  <span>Belum</span>
                </>
              )}
            </div>
            {todayStatus?.clock_in_time && (
              <div className="text-sm text-gray-500 mt-2">
                {new Date(todayStatus.clock_in_time).toLocaleTimeString('id-ID', { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </div>
            )}
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-2">Clock Out</div>
            <div className="text-xl md:text-2xl font-bold text-gray-800 flex items-center gap-2">
              {todayStatus?.has_clocked_out ? (
                <>
                  <CheckCircle className="w-6 h-6 text-green-500" />
                  <span>Sudah</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-6 h-6 text-red-500" />
                  <span>Belum</span>
                </>
              )}
            </div>
            {todayStatus?.clock_out_time && (
              <div className="text-sm text-gray-500 mt-2">
                {new Date(todayStatus.clock_out_time).toLocaleTimeString('id-ID', { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Location Section */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6 mb-4 md:mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg md:text-xl font-semibold text-gray-800 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-blue-500" />
            Lokasi GPS
          </h2>
          <Button
            variant="outline"
            size="sm"
            onClick={getCurrentLocation}
            disabled={locationLoading}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${locationLoading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </Button>
        </div>
        
        {locationLoading ? (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner />
            <span className="ml-3 text-gray-600">Mengambil lokasi...</span>
          </div>
        ) : location.lat && location.lng ? (
          <div className="space-y-2">
            <div className="bg-gray-50 rounded-lg p-3 md:p-4">
              <div className="text-xs md:text-sm text-gray-500 mb-1">Koordinat</div>
              <div className="text-sm md:text-base font-mono text-gray-800">
                {location.lat.toFixed(6)}, {location.lng.toFixed(6)}
              </div>
            </div>
            {location.address && (
              <div className="bg-gray-50 rounded-lg p-3 md:p-4">
                <div className="text-xs md:text-sm text-gray-500 mb-1">Alamat</div>
                <div className="text-sm md:text-base text-gray-800">{location.address}</div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <AlertCircle className="w-12 h-12 text-yellow-500 mx-auto mb-2" />
            <p className="text-sm md:text-base text-yellow-600 mb-4">
              {locationError || 'Lokasi belum diambil'}
            </p>
            <Button
              variant="primary"
              onClick={getCurrentLocation}
              disabled={locationLoading}
              className="flex items-center gap-2 mx-auto"
            >
              <MapPin className="w-4 h-4" />
              Ambil Lokasi GPS
            </Button>
          </div>
        )}
      </div>

      {/* Camera Section */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6 mb-4 md:mb-6">
        <h2 className="text-lg md:text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <Camera className="w-5 h-5 text-purple-500" />
          Foto Selfie
        </h2>
        
        {cameraOpen ? (
          <div className="space-y-4">
            <div className="relative bg-black rounded-lg overflow-hidden" style={{ aspectRatio: '4/3' }}>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
                style={{ 
                  transform: 'scaleX(-1)', // Mirror effect untuk selfie
                  minHeight: '300px'
                }}
              />
              <div className="absolute inset-0 pointer-events-none border-4 border-white/20 rounded-lg"></div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs md:text-sm text-blue-700 text-center">
                📸 Posisikan diri Anda dengan baik, lalu klik "Ambil Foto"
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-2">
              <Button
                variant="primary"
                onClick={capturePhoto}
                className="flex-1 flex items-center justify-center gap-2 py-3"
              >
                <Camera className="w-5 h-5" />
                <span className="font-semibold">Ambil Foto</span>
              </Button>
              <Button
                variant="outline"
                onClick={closeCamera}
                className="flex-1 flex items-center justify-center gap-2 py-3"
              >
                <X className="w-5 h-5" />
                <span>Batal</span>
              </Button>
            </div>
          </div>
        ) : capturedPhoto ? (
          <div className="space-y-4">
            <div className="relative bg-gray-100 rounded-lg overflow-hidden" style={{ aspectRatio: '4/3' }}>
              <img 
                src={capturedPhoto} 
                alt="Captured photo" 
                className="w-full h-full object-cover"
              />
            </div>
            <Button
              variant="outline"
              onClick={() => {
                setCapturedPhoto(null);
                openCamera();
              }}
              className="w-full flex items-center justify-center gap-2"
            >
              <Camera className="w-4 h-4" />
              Ambil Ulang
            </Button>
          </div>
        ) : (
          <div className="text-center py-8">
            <Camera className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-sm md:text-base text-gray-600 mb-4">Foto belum diambil</p>
            <Button
              variant="primary"
              onClick={openCamera}
              className="flex items-center gap-2 mx-auto"
            >
              <Camera className="w-4 h-4" />
              Buka Kamera
            </Button>
          </div>
        )}
      </div>

      {/* Hidden canvas for photo capture */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Notes Section */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6 mb-4 md:mb-6">
        <label className="block text-sm md:text-base font-medium text-gray-700 mb-2">
          Catatan (Opsional)
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
          className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-vertical text-sm md:text-base"
          placeholder="Tambahkan catatan jika diperlukan..."
        />
      </div>

      {/* Action Buttons */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
        {canClockIn ? (
          <Button
            variant="primary"
            onClick={handleClockIn}
            isLoading={clockingIn}
            disabled={!location.lat || !location.lng || !capturedPhoto}
            className="w-full flex items-center justify-center gap-2 py-3 text-base md:text-lg"
          >
            <CheckCircle className="w-5 h-5" />
            Clock In
          </Button>
        ) : canClockOut ? (
          <Button
            variant="primary"
            onClick={handleClockOut}
            isLoading={clockingOut}
            disabled={!location.lat || !location.lng || !capturedPhoto}
            className="w-full flex items-center justify-center gap-2 py-3 text-base md:text-lg"
          >
            <CheckCircle className="w-5 h-5" />
            Clock Out
          </Button>
        ) : (
          <div className="text-center py-4">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
            <p className="text-sm md:text-base text-gray-600">
              Absensi hari ini sudah selesai
            </p>
          </div>
        )}
      </div>

      {/* Help Text */}
      <div className="mt-4 md:mt-6 bg-blue-50 rounded-lg p-4 md:p-6">
        <h3 className="text-sm md:text-base font-semibold text-blue-800 mb-2">Petunjuk Penggunaan:</h3>
        <ul className="text-xs md:text-sm text-blue-700 space-y-1 list-disc list-inside">
          <li>Pastikan GPS dan kamera sudah diizinkan di browser</li>
          <li>Lokasi GPS akan diambil otomatis saat halaman dimuat</li>
          <li>Ambil foto selfie sebagai bukti kehadiran</li>
          <li>Klik Clock In untuk memulai kerja</li>
          <li>Klik Clock Out untuk mengakhiri kerja</li>
        </ul>
      </div>
    </div>
  );
};

export default AttendanceClockInPage;

