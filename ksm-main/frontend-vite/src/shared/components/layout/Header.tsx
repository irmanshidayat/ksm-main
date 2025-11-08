/**
 * Header Component
 * Main header component untuk layout
 */

import React from 'react';
import { useAppSelector, useAppDispatch } from '@/app/store/hooks';
import { toggleSidebar } from '@/app/store/slices/uiSlice';

const Header: React.FC = () => {
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);
  const { sidebarOpen } = useAppSelector((state) => state.ui);

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 h-[60px] flex items-center justify-between px-4">
      <div className="flex items-center">
        <button
          onClick={() => dispatch(toggleSidebar())}
          className="p-2 rounded-md text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
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
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
        <h1 className="ml-4 text-xl font-semibold text-gray-800">KSM Main</h1>
      </div>
      
      <div className="flex items-center space-x-4">
        {user && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-800">{user.username}</span>
            <span className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
              {user.role}
            </span>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;

