/**
 * Enhanced Notion Tasks Types
 */

export interface NotionTask {
  id: string;
  employee_name: string;
  title: string;
  date: string;
  status: string;
  priority: string;
  description: string;
  notion_url: string;
  created_time: string;
  last_edited_time: string;
}

export interface EmployeeStatistics {
  total_employees: number;
  total_tasks: number;
  tasks_by_status: Record<string, number>;
  tasks_by_priority: Record<string, number>;
  last_sync: string;
}

export interface Employee {
  name: string;
  task_count: number;
}

export interface NotionTasksQueryParams {
  employee?: string;
  status?: string;
  priority?: string;
  date_from?: string;
  date_to?: string;
}

