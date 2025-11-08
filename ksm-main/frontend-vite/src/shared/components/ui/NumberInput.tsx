/**
 * NumberInput Component
 * Input component untuk number yang mempertahankan nilai exact yang diketik user
 * Tidak akan mengubah/membulatkan nilai yang diinput
 * 
 * Component ini menggunakan type="text" dengan validasi untuk mempertahankan
 * nilai exact yang diketik user, menghindari masalah formatting dari type="number"
 */

import React, { useState, useEffect } from 'react';
import Input, { InputProps } from './Input';

export interface NumberInputProps extends Omit<InputProps, 'type' | 'value' | 'onChange'> {
  value?: number | string;
  onChange?: (value: number | string) => void;
  returnAsString?: boolean; // Jika true, onChange akan return string, jika false akan return number
  allowEmpty?: boolean; // Jika true, akan allow empty string
}

const NumberInput: React.FC<NumberInputProps> = ({
  value,
  onChange,
  returnAsString = false,
  allowEmpty = false,
  step,
  min,
  max,
  ...props
}) => {
  // Store the raw string value that user types
  const [displayValue, setDisplayValue] = useState<string>('');

  // Initialize display value when prop value changes
  useEffect(() => {
    if (value === undefined || value === null) {
      setDisplayValue(allowEmpty ? '' : '0');
    } else {
      // Convert to string, preserving exact representation
      // Use toFixed only if it's a decimal and we need to preserve decimals
      const stringValue = typeof value === 'string' 
        ? value 
        : (step && String(step).includes('.') && value % 1 !== 0)
          ? value.toFixed(String(step).split('.')[1]?.length || 2)
          : String(value);
      setDisplayValue(stringValue);
    }
  }, [value, allowEmpty, step]);

  const isValidNumber = (str: string): boolean => {
    if (str === '' || str === '-') return false;
    // Allow numbers with optional decimal point
    const numberRegex = /^-?\d*\.?\d*$/;
    return numberRegex.test(str);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const rawValue = e.target.value;
    
    // Only allow valid number input
    if (rawValue === '' && allowEmpty) {
      setDisplayValue('');
      onChange?.(returnAsString ? '' : 0);
      return;
    }

    if (rawValue === '') {
      setDisplayValue('0');
      onChange?.(returnAsString ? '0' : 0);
      return;
    }

    // Validate input
    if (!isValidNumber(rawValue)) {
      // Don't update if invalid
      return;
    }

    // Always update display with what user types
    setDisplayValue(rawValue);

    // Convert to number only for the onChange callback if needed
    if (returnAsString) {
      onChange?.(rawValue);
    } else {
      // Try to parse to number for onChange callback
      const numValue = rawValue.includes('.') 
        ? parseFloat(rawValue) 
        : parseInt(rawValue, 10);
      
      if (!isNaN(numValue)) {
        // Validate min/max if provided
        let finalValue = numValue;
        if (min !== undefined && numValue < Number(min)) {
          finalValue = Number(min);
          setDisplayValue(String(finalValue));
        }
        if (max !== undefined && numValue > Number(max)) {
          finalValue = Number(max);
          setDisplayValue(String(finalValue));
        }
        onChange?.(finalValue);
      }
    }
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    // On blur, ensure we have a valid number
    const rawValue = e.target.value.trim();
    
    if (allowEmpty && rawValue === '') {
      return;
    }

    if (rawValue === '' || rawValue === '-') {
      const defaultValue = '0';
      setDisplayValue(defaultValue);
      onChange?.(returnAsString ? defaultValue : 0);
      return;
    }

    // Validate the number
    const numValue = rawValue.includes('.') 
      ? parseFloat(rawValue) 
      : parseInt(rawValue, 10);
    
    if (isNaN(numValue)) {
      const defaultValue = '0';
      setDisplayValue(defaultValue);
      onChange?.(returnAsString ? defaultValue : 0);
    } else {
      // Keep the exact string representation user typed
      // Don't reformat it unless we need to apply min/max
      let finalValue = numValue;
      let finalString = rawValue;
      
      if (min !== undefined && numValue < Number(min)) {
        finalValue = Number(min);
        finalString = String(finalValue);
      }
      if (max !== undefined && numValue > Number(max)) {
        finalValue = Number(max);
        finalString = String(finalValue);
      }
      
      setDisplayValue(finalString);
      if (!returnAsString) {
        onChange?.(finalValue);
      } else {
        onChange?.(finalString);
      }
    }
  };

  return (
    <Input
      type="text"
      inputMode="decimal"
      value={displayValue}
      onChange={handleChange}
      onBlur={handleBlur}
      {...props}
    />
  );
};

export default NumberInput;

