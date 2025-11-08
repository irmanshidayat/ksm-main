/**
 * Database Discovery Types
 */

export interface DatabaseInfo {
  id: number;
  database_id: string;
  database_title: string;
  employee_name: string | null;
  database_type: string;
  is_task_database: boolean;
  is_employee_specific: boolean;
  structure_valid: boolean;
  confidence_score: number;
  missing_properties: string[];
  sync_enabled: boolean;
  last_synced: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmployeeStats {
  employee_name: string;
  total_databases: number;
  task_databases: number;
  valid_databases: number;
  average_confidence: number;
}

export interface DiscoveryStatistics {
  total_databases: number;
  task_databases: number;
  employee_databases: number;
  valid_databases: number;
  enabled_databases: number;
}

export interface DatabaseDiscoveryQueryParams {
  type?: string;
  employee?: string;
  valid_only?: boolean;
}

