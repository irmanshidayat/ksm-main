/**
 * Sidebar Component
 * Main sidebar navigation component - Dinamis dan Responsif dengan Submenu
 */

import React, { useMemo, useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '@/app/store/hooks';
import { setSidebarOpen } from '@/app/store/slices/uiSlice';
import { useGetUserMenusQuery } from '@/features/permission-management/store/permissionApi';
import { useAuth } from '@/features/auth/hooks/useAuth';

interface SubMenuItem {
  name: string;
  path: string;
}

interface NavigationItem {
  name: string;
  path?: string;
  icon: string;
  submenu?: SubMenuItem[];
}

interface MenuFromAPI {
  id: number;
  name: string;
  path: string;
  icon: string;
  parent_id: number | null;
  order_index: number;
  sub_menus?: MenuFromAPI[];
}

const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { sidebarOpen } = useAppSelector((state) => state.ui);
  const { user } = useAppSelector((state) => state.auth);
  const { logout } = useAuth();
  const [expandedMenus, setExpandedMenus] = useState<Set<string>>(new Set());
  
  // Fetch menus from API dengan auto-refresh setelah update
  const { 
    data: menusFromAPI, 
    isLoading: isLoadingMenus, 
    error: menusError,
    isError: isMenusError 
  } = useGetUserMenusQuery(undefined, {
    // Refetch saat window focus untuk update real-time setelah update sidebar visibility
    refetchOnFocus: true,
    // Refetch saat reconnect
    refetchOnReconnect: true,
  });

  // Convert API menu format to NavigationItem format
  const convertMenuToNavigationItem = (menu: MenuFromAPI): NavigationItem => {
    const submenu: SubMenuItem[] = menu.sub_menus?.map(sub => ({
      name: sub.name,
      path: sub.path,
    })) || [];

    return {
      name: menu.name,
      path: submenu.length > 0 ? undefined : menu.path,
      icon: menu.icon || '📄',
      submenu: submenu.length > 0 ? submenu : undefined
    };
  };

  // Menu dinamis dari database - 100% dari API, tidak ada fallback hardcoded
  const navigation: NavigationItem[] = useMemo(() => {
    try {
      // Log untuk debugging
      if (menusFromAPI !== undefined) {
        console.log('[Sidebar] Menus from API:', {
          count: menusFromAPI?.length || 0,
          data: menusFromAPI,
          user: user?.username || 'Unknown',
          userId: user?.id || 'Unknown'
        });
      }

      // Jika API return data, gunakan data dari API
      if (menusFromAPI && menusFromAPI.length > 0) {
        const convertedMenus = menusFromAPI.map(convertMenuToNavigationItem);
        console.log('[Sidebar] Converted menus:', convertedMenus);
        return convertedMenus;
      }
      
      // Jika tidak ada data dari API, return empty array (tidak ada fallback hardcoded)
      if (menusFromAPI !== undefined && menusFromAPI.length === 0) {
        console.warn('[Sidebar] No menus available for user:', {
          userId: user?.id,
          username: user?.username,
          role: user?.role
        });
      }
      
      return [];
    } catch (error) {
      console.error('[Sidebar] Error processing menus from API:', error);
      return [];
    }
  }, [menusFromAPI, user]);

  // Auto-expand submenu yang memiliki halaman aktif
  useEffect(() => {
    setExpandedMenus(prev => {
      const newSet = new Set(prev);
      navigation.forEach(item => {
        if (item.submenu && item.submenu.length > 0) {
          const hasActiveSubmenu = item.submenu.some(
            sub => location.pathname === sub.path || location.pathname.startsWith(sub.path + '/')
          );
          if (hasActiveSubmenu) {
            newSet.add(item.name);
          }
        }
      });
      return newSet;
    });
  }, [location.pathname, navigation]);

  // Toggle expand/collapse submenu
  const toggleSubmenu = (menuName: string) => {
    setExpandedMenus(prev => {
      const newSet = new Set(prev);
      if (newSet.has(menuName)) {
        newSet.delete(menuName);
      } else {
        newSet.add(menuName);
      }
      return newSet;
    });
  };

  // Check if menu should be expanded (if any submenu item is active)
  const isMenuExpanded = (item: NavigationItem) => {
    if (!item.submenu) return false;
    return expandedMenus.has(item.name) || 
           item.submenu.some(sub => location.pathname === sub.path || location.pathname.startsWith(sub.path + '/'));
  };

  // Check if menu or submenu is active
  const isMenuActive = (item: NavigationItem) => {
    if (item.path) {
      return location.pathname === item.path || location.pathname.startsWith(item.path + '/');
    }
    if (item.submenu) {
      return item.submenu.some(sub => location.pathname === sub.path || location.pathname.startsWith(sub.path + '/'));
    }
    return false;
  };

  // Close sidebar saat klik menu (hanya untuk mobile/tablet)
  const handleLinkClick = () => {
    // Hanya close di mobile/tablet (screen < 1024px)
    if (window.innerWidth < 1024) {
      dispatch(setSidebarOpen(false));
    }
  };

  // Close sidebar saat klik overlay
  const handleOverlayClick = () => {
    dispatch(setSidebarOpen(false));
  };

  // Close sidebar button
  const handleCloseClick = () => {
    dispatch(setSidebarOpen(false));
  };

  // Handle logout
  const handleLogout = () => {
    logout();
    navigate('/login');
    dispatch(setSidebarOpen(false));
  };

  return (
    <>
      {/* Overlay untuk mobile/tablet saja */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden transition-opacity"
          onClick={handleOverlayClick}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          bg-white border-r border-gray-200 shadow-lg text-gray-700 w-[250px] min-h-screen 
          transition-transform duration-300 ease-in-out
          fixed top-0 left-0 z-50
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0 lg:static lg:z-auto
        `}
      >
        {/* Header dengan close button untuk semua ukuran */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">Menu</h2>
          <button
            onClick={handleCloseClick}
            className="p-2 rounded-md text-gray-500 hover:bg-gray-100 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors lg:hidden"
            aria-label="Close sidebar"
          >
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* User info untuk semua ukuran */}
        {user && (
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
                  <span className="text-primary-600 font-semibold text-sm">
                    {user.username?.charAt(0).toUpperCase() || 'U'}
                  </span>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">
                  {user.username || 'User'}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {user.role || 'User'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav className="p-4 overflow-y-auto max-h-[calc(100vh-120px)]">
          <ul className="space-y-1">
            {isLoadingMenus ? (
              <li className="text-sm text-gray-500 p-4 text-center">Memuat menu...</li>
            ) : isMenusError ? (
              <li className="text-sm text-red-600 p-4 text-center">
                <div className="space-y-2">
                  <p className="font-medium">Gagal memuat menu</p>
                  <p className="text-xs text-gray-500">
                    {menusError && 'data' in menusError 
                      ? (menusError.data as any)?.error || 'Terjadi kesalahan saat mengambil menu'
                      : 'Terjadi kesalahan saat mengambil menu'}
                  </p>
                  <button
                    onClick={() => window.location.reload()}
                    className="text-xs text-primary-600 hover:text-primary-700 underline mt-2"
                  >
                    Coba muat ulang
                  </button>
                </div>
              </li>
            ) : navigation.length === 0 ? (
              <li className="text-sm text-gray-500 p-4 text-center">
                <div className="space-y-2">
                  <p>Tidak ada menu tersedia.</p>
                  <p className="text-xs">
                    Silakan hubungi administrator untuk mendapatkan akses menu.
                  </p>
                  {user && (
                    <p className="text-xs text-gray-400 mt-2">
                      User: {user.username} | Role: {user.role || 'Tidak ada role'}
                    </p>
                  )}
                </div>
              </li>
            ) : (
              navigation.map((item) => {
                const hasSubmenu = item.submenu && item.submenu.length > 0;
                const isExpanded = isMenuExpanded(item);
                const isActive = isMenuActive(item);

                return (
                  <li key={item.name}>
                    {hasSubmenu ? (
                      <>
                        <button
                          onClick={() => toggleSubmenu(item.name)}
                          className={`
                            w-full flex items-center justify-between px-4 py-2 rounded-lg transition-colors
                            ${
                              isActive
                                ? 'bg-primary-600 text-white shadow-md'
                                : 'text-gray-700 hover:bg-primary-50 hover:text-primary-600'
                            }
                          `}
                        >
                          <div className="flex items-center space-x-3">
                            <span className="text-xl">{item.icon}</span>
                            <span className="font-medium">{item.name}</span>
                          </div>
                          <svg
                            className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 9l-7 7-7-7"
                            />
                          </svg>
                        </button>
                        {isExpanded && item.submenu && (
                          <ul className="mt-1 ml-4 space-y-1 border-l-2 border-gray-200 pl-2">
                            {item.submenu.map((subItem) => {
                              const isSubActive = location.pathname === subItem.path || location.pathname.startsWith(subItem.path + '/');
                              return (
                                <li key={subItem.path}>
                                  <Link
                                    to={subItem.path}
                                    onClick={handleLinkClick}
                                    className={`
                                      flex items-center px-4 py-2 rounded-lg transition-colors text-sm
                                      ${
                                        isSubActive
                                          ? 'bg-primary-600 text-white shadow-md font-medium'
                                          : 'text-gray-600 hover:bg-primary-50 hover:text-primary-600'
                                      }
                                    `}
                                  >
                                    <span className="ml-2">{subItem.name}</span>
                                  </Link>
                                </li>
                              );
                            })}
                          </ul>
                        )}
                      </>
                    ) : (
                      <Link
                        to={item.path || '#'}
                        onClick={handleLinkClick}
                        className={`
                          flex items-center space-x-3 px-4 py-2 rounded-lg transition-colors
                          ${
                            isActive
                              ? 'bg-primary-600 text-white shadow-md'
                              : 'text-gray-700 hover:bg-primary-50 hover:text-primary-600'
                          }
                        `}
                      >
                        <span className="text-xl">{item.icon}</span>
                        <span className="font-medium">{item.name}</span>
                      </Link>
                    )}
                  </li>
                );
              })
            )}
            
            {/* Logout Button - Muncul di akhir scrollable menu */}
            <li className="mt-4 pt-4 border-t border-gray-200">
              <button
                onClick={handleLogout}
                className="
                  w-full flex items-center space-x-3 px-4 py-2 rounded-lg transition-colors
                  text-gray-700 hover:bg-red-50 hover:text-red-600
                "
              >
                <span className="text-xl">🚪</span>
                <span className="font-medium">Logout</span>
              </button>
            </li>
          </ul>
        </nav>
      </aside>
    </>
  );
};

export default Sidebar;

