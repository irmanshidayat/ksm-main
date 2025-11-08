/**
 * Checkbox Component
 * Reusable checkbox component dengan Tailwind CSS
 */

import React from 'react';

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Checkbox: React.FC<CheckboxProps> = ({
  label,
  error,
  className = '',
  id,
  ...props
}) => {
  const inputId = id || `checkbox-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="w-full">
      <div className="flex items-center">
        <input
          id={inputId}
          type="checkbox"
          className={`
            h-4 w-4 text-primary-600 focus:ring-primary-500 border-border-medium rounded
            ${error ? 'border-danger' : ''}
            ${className}
          `}
          {...props}
        />
        {label && (
          <label htmlFor={inputId} className="ml-2 text-sm text-text-primary">
            {label}
          </label>
        )}
      </div>
      {error && <p className="mt-1 text-sm text-danger">{error}</p>}
    </div>
  );
};

export default Checkbox;

