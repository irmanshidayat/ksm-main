/**
 * Radio Component
 * Reusable radio component dengan Tailwind CSS
 */

import React from 'react';

export interface RadioProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Radio: React.FC<RadioProps> = ({
  label,
  error,
  className = '',
  id,
  ...props
}) => {
  const inputId = id || `radio-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="w-full">
      <div className="flex items-center">
        <input
          id={inputId}
          type="radio"
          className={`
            h-4 w-4 text-primary-600 focus:ring-primary-500 border-border-medium
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

export default Radio;

