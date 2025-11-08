/**
 * Tailwind Helpers
 * Helper functions untuk memudahkan penggunaan Tailwind classes
 */

/**
 * Combine multiple class names dengan handling conditional classes
 */
export const cn = (...classes: (string | undefined | null | false)[]): string => {
  return classes.filter(Boolean).join(' ');
};

/**
 * Build responsive classes dengan mobile-first approach
 */
export const responsive = {
  mobile: (classes: string) => classes,
  tablet: (classes: string) => `tablet:${classes}`,
  desktop: (classes: string) => `desktop:${classes}`,
  wide: (classes: string) => `wide:${classes}`,
};

/**
 * Build spacing utilities
 */
export const spacing = {
  xs: 'p-xs',
  sm: 'p-sm',
  md: 'p-md',
  lg: 'p-lg',
  xl: 'p-xl',
  '2xl': 'p-2xl',
  '3xl': 'p-3xl',
};

/**
 * Build color utilities untuk semantic colors
 */
export const colors = {
  primary: 'text-primary bg-primary',
  secondary: 'text-secondary bg-secondary',
  success: 'text-success bg-success',
  warning: 'text-warning bg-warning',
  danger: 'text-danger bg-danger',
  info: 'text-info bg-info',
};

/**
 * Build shadow utilities
 */
export const shadows = {
  sm: 'shadow-sm',
  md: 'shadow-md',
  lg: 'shadow-lg',
  xl: 'shadow-xl',
};

/**
 * Build border radius utilities
 */
export const radius = {
  sm: 'rounded-sm',
  md: 'rounded-md',
  lg: 'rounded-lg',
  xl: 'rounded-xl',
  '2xl': 'rounded-2xl',
  full: 'rounded-full',
};

/**
 * Build transition utilities
 */
export const transitions = {
  fast: 'transition-fast',
  normal: 'transition-normal',
  slow: 'transition-slow',
  all: 'transition-all',
  colors: 'transition-colors',
  opacity: 'transition-opacity',
  transform: 'transition-transform',
};

/**
 * Build z-index utilities
 */
export const zIndex = {
  dropdown: 'z-dropdown',
  sticky: 'z-sticky',
  fixed: 'z-fixed',
  'modal-backdrop': 'z-modal-backdrop',
  modal: 'z-modal',
  popover: 'z-popover',
  tooltip: 'z-tooltip',
};

/**
 * Build flex utilities
 */
export const flex = {
  center: 'flex items-center justify-center',
  between: 'flex items-center justify-between',
  start: 'flex items-center justify-start',
  end: 'flex items-center justify-end',
  col: 'flex flex-col',
  row: 'flex flex-row',
};

/**
 * Build grid utilities
 */
export const grid = {
  '1': 'grid grid-cols-1',
  '2': 'grid grid-cols-2',
  '3': 'grid grid-cols-3',
  '4': 'grid grid-cols-4',
  '12': 'grid grid-cols-12',
  responsive: 'grid grid-cols-1 tablet:grid-cols-2 desktop:grid-cols-3',
};

/**
 * Build text utilities
 */
export const text = {
  xs: 'text-xs',
  sm: 'text-sm',
  base: 'text-base',
  lg: 'text-lg',
  xl: 'text-xl',
  '2xl': 'text-2xl',
  '3xl': 'text-3xl',
  '4xl': 'text-4xl',
  primary: 'text-text-primary',
  secondary: 'text-text-secondary',
  muted: 'text-text-muted',
  white: 'text-text-white',
};

/**
 * Build background utilities
 */
export const bg = {
  primary: 'bg-bg-primary',
  secondary: 'bg-bg-secondary',
  tertiary: 'bg-bg-tertiary',
  light: 'bg-bg-light',
};

/**
 * Build border utilities
 */
export const border = {
  light: 'border-border-light',
  medium: 'border-border-medium',
  dark: 'border-border-dark',
  all: 'border',
  top: 'border-t',
  bottom: 'border-b',
  left: 'border-l',
  right: 'border-r',
};

/**
 * Helper untuk build table classes
 */
export const tableClasses = {
  container: 'overflow-x-auto',
  table: 'min-w-full divide-y divide-border-light bg-white',
  thead: 'bg-bg-secondary',
  th: 'px-6 py-3 text-left text-xs font-semibold text-text-primary uppercase tracking-wider',
  tbody: 'bg-white divide-y divide-border-light',
  tr: {
    base: 'bg-white',
    striped: 'bg-bg-secondary',
    hover: 'hover:bg-primary-50 cursor-pointer transition-colors',
  },
  td: 'px-6 py-4 whitespace-nowrap text-sm text-text-primary',
};

/**
 * Helper untuk build modal classes
 */
export const modalClasses = {
  backdrop: 'fixed inset-0 z-modal-backdrop bg-black bg-opacity-50 flex items-center justify-center p-4',
  container: 'bg-white rounded-lg shadow-xl w-full max-h-[90vh] flex flex-col',
  header: 'flex items-center justify-between px-6 py-4 border-b border-border-light',
  body: 'flex-1 overflow-y-auto px-6 py-4',
  footer: 'px-6 py-4 border-t border-border-light flex items-center justify-end gap-2',
};

/**
 * Helper untuk build card classes
 */
export const cardClasses = {
  container: 'bg-white rounded-lg shadow-md border border-border-light',
  header: 'px-6 py-4 border-b border-border-light',
  body: 'px-6 py-4',
  footer: 'px-6 py-4 border-t border-border-light',
  hover: 'hover:shadow-lg transition-shadow cursor-pointer',
};

/**
 * Helper untuk build button classes
 */
export const buttonClasses = {
  base: 'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed',
  primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
  secondary: 'bg-secondary text-white hover:bg-gray-700 focus:ring-gray-500',
  danger: 'bg-danger text-white hover:bg-red-700 focus:ring-red-500',
  outline: 'border-2 border-primary-600 text-primary-600 hover:bg-primary-50 focus:ring-primary-500',
  ghost: 'text-primary-600 hover:bg-primary-50 focus:ring-primary-500',
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg',
};

/**
 * Helper untuk build input classes
 */
export const inputClasses = {
  base: 'block w-full px-3 py-2 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors',
  normal: 'border-border-medium',
  error: 'border-danger focus:ring-danger focus:border-danger',
};

export default {
  cn,
  responsive,
  spacing,
  colors,
  shadows,
  radius,
  transitions,
  zIndex,
  flex,
  grid,
  text,
  bg,
  border,
  tableClasses,
  modalClasses,
  cardClasses,
  buttonClasses,
  inputClasses,
};

