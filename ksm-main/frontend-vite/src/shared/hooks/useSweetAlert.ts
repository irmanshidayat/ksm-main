/**
 * useSweetAlert Hook
 * Hook untuk menggunakan SweetAlert2
 */

import Swal from 'sweetalert2';

export const useSweetAlert = () => {
  const showSuccess = async (title: string, text: string) => {
    await Swal.fire({
      icon: 'success',
      title,
      text,
      confirmButtonText: 'OK',
    });
  };

  const showSuccessAuto = async (title: string, text: string, timer: number = 2000) => {
    await Swal.fire({
      icon: 'success',
      title,
      text,
      timer,
      timerProgressBar: true,
      showConfirmButton: false,
    });
  };

  const showError = async (title: string, text: string) => {
    await Swal.fire({
      icon: 'error',
      title,
      text,
      confirmButtonText: 'OK',
    });
  };

  const showWarning = async (title: string, text: string) => {
    await Swal.fire({
      icon: 'warning',
      title,
      text,
      confirmButtonText: 'OK',
    });
  };

  const showInfo = async (title: string, text: string) => {
    await Swal.fire({
      icon: 'info',
      title,
      text,
      confirmButtonText: 'OK',
    });
  };

  const showConfirm = async (title: string, text: string): Promise<boolean> => {
    const result = await Swal.fire({
      icon: 'question',
      title,
      text,
      showCancelButton: true,
      confirmButtonText: 'Ya',
      cancelButtonText: 'Tidak',
    });
    return result.isConfirmed;
  };

  const showLoading = (title: string, text: string) => {
    Swal.fire({
      title,
      text,
      allowOutsideClick: false,
      allowEscapeKey: false,
      showConfirmButton: false,
      didOpen: () => {
        Swal.showLoading();
      },
    });
  };

  const hideLoading = () => {
    Swal.close();
  };

  return {
    showSuccess,
    showSuccessAuto,
    showError,
    showWarning,
    showInfo,
    showConfirm,
    showLoading,
    hideLoading,
  };
};

