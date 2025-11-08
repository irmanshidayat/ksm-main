/**
 * Table Component
 * Reusable table component dengan Tailwind CSS
 */

import React from 'react';

export interface TableColumn<T = any> {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  className?: string;
  headerClassName?: string;
}

export interface TableProps<T = any> {
  data: T[];
  columns: TableColumn<T>[];
  loading?: boolean;
  emptyMessage?: string;
  onRowClick?: (record: T, index: number) => void;
  className?: string;
  striped?: boolean;
  hoverable?: boolean;
}

const Table = <T extends Record<string, any>>({
  data,
  columns,
  loading = false,
  emptyMessage = 'Tidak ada data',
  onRowClick,
  className = '',
  striped = true,
  hoverable = true,
  children,
}: TableProps<T> & { children?: React.ReactNode }) => {
  // Jika children ada, gunakan sebagai wrapper untuk table element
  if (children !== undefined) {
    return (
      <div className={`overflow-x-auto ${className}`}>
        <table className="min-w-full divide-y divide-border-light bg-white">
          {children}
        </table>
      </div>
    );
  }

  // Jika tidak ada children, gunakan mode data-driven
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Handle undefined or null data
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="text-center py-12 text-text-secondary">
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="min-w-full divide-y divide-border-light bg-white">
        <thead className="bg-bg-secondary">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={`px-6 py-3 text-left text-xs font-semibold text-text-primary uppercase tracking-wider ${
                  column.headerClassName || ''
                }`}
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className={`bg-white divide-y divide-border-light ${striped ? 'divide-y' : ''}`}>
          {data.map((record, rowIndex) => (
            <tr
              key={rowIndex}
              onClick={() => onRowClick?.(record, rowIndex)}
              className={`
                ${striped && rowIndex % 2 === 0 ? 'bg-bg-secondary' : 'bg-white'}
                ${hoverable ? 'hover:bg-primary-50 cursor-pointer transition-colors' : ''}
                ${onRowClick ? 'cursor-pointer' : ''}
              `}
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={`px-6 py-4 whitespace-nowrap text-sm text-text-primary ${column.className || ''}`}
                >
                  {column.render
                    ? column.render(record[column.key], record, rowIndex)
                    : record[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Sub-components untuk compound pattern
Table.Header = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <thead className={`bg-bg-secondary ${className}`}>{children}</thead>
);

Table.Body = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <tbody className={`bg-white divide-y divide-border-light ${className}`}>{children}</tbody>
);

Table.Row = ({ 
  children, 
  className = '', 
  onClick 
}: { 
  children: React.ReactNode; 
  className?: string;
  onClick?: () => void;
}) => (
  <tr 
    className={`${onClick ? 'cursor-pointer hover:bg-primary-50 transition-colors' : ''} ${className}`}
    onClick={onClick}
  >
    {children}
  </tr>
);

Table.Head = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <th className={`px-6 py-3 text-left text-xs font-semibold text-text-primary uppercase tracking-wider ${className}`}>
    {children}
  </th>
);

Table.Cell = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <td className={`px-6 py-4 whitespace-nowrap text-sm text-text-primary ${className}`}>
    {children}
  </td>
);

export default Table;

