/**
 * App Providers
 * Wrapper untuk semua providers (Redux, Router, dll)
 */

import { Provider } from 'react-redux';
import { store } from '../store';
import AuthProvider from './AuthProvider';
import AppRouter from '../router';

interface AppProvidersProps {
  children?: React.ReactNode;
}

const AppProviders: React.FC<AppProvidersProps> = () => {
  return (
    <Provider store={store}>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </Provider>
  );
};

export default AppProviders;

