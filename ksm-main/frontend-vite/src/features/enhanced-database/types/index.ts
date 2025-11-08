/**
 * Enhanced Database Types
 */

export interface DatabaseInfo {
  id: string;
  database_id: string;
  database_title: string;
  employee_name: string;
  database_type: string;
  is_task_database: boolean;
  is_employee_specific: boolean;
  structure_valid: boolean;
  confidence_score: number;
  mapping_quality_score: number;
  mapped_properties_count: number;
  last_mapping_analysis: string;
  sync_enabled: boolean;
  mapping_statistics?: {
    total_mappings: number;
    active_mappings: number;
    required_mappings: number;
    high_confidence_mappings: number;
    mapping_quality_score: number;
  };
}

export interface PropertyMapping {
  id: number;
  database_id: string;
  notion_property_name: string;
  property_type: string;
  mapped_field: string;
  confidence_score: number;
  alternative_names: string[];
  is_required: boolean;
  validation_rules: any;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MappingStatistics {
  total_databases: number;
  total_mappings: number;
  active_mappings: number;
  high_quality_mappings: number;
  average_mappings_per_database: number;
  mapping_coverage_percentage: number;
}

