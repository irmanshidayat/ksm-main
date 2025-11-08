/**
 * Card Component
 * Reusable card component dengan Tailwind CSS
 */

import React from 'react';

export interface CardProps {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
  headerClassName?: string;
  bodyClassName?: string;
  footerClassName?: string;
  hoverable?: boolean;
  onClick?: () => void;
}

const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  children,
  footer,
  className = '',
  headerClassName = '',
  bodyClassName = '',
  footerClassName = '',
  hoverable = false,
  onClick,
}) => {
  return (
    <div
      className={`
        bg-white rounded-lg shadow-md border border-border-light
        ${hoverable ? 'hover:shadow-lg transition-shadow cursor-pointer' : ''}
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
      onClick={onClick}
    >
      {/* Header */}
      {(title || subtitle) && (
        <div className={`px-6 py-4 border-b border-border-light ${headerClassName}`}>
          {title && <h3 className="text-lg font-semibold text-text-primary">{title}</h3>}
          {subtitle && <p className="text-sm text-text-secondary mt-1">{subtitle}</p>}
        </div>
      )}

      {/* Body */}
      <div className={`px-6 py-4 ${bodyClassName}`}>{children}</div>

      {/* Footer */}
      {footer && (
        <div className={`px-6 py-4 border-t border-border-light ${footerClassName}`}>
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;

