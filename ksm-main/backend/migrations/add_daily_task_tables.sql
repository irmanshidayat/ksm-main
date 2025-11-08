-- Migration: Add Daily Task Tables
-- Description: Create tables for daily task management system
-- Date: 2024-01-01
-- Author: KSM Development Team

-- Create daily_tasks table
CREATE TABLE IF NOT EXISTS `daily_tasks` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `user_id` int(11) NOT NULL,
    `task_date` date NOT NULL,
    `title` varchar(200) NOT NULL,
    `description` text,
    `category` varchar(20) DEFAULT 'regular',
    `priority` varchar(20) DEFAULT 'medium',
    `status` varchar(20) DEFAULT 'todo',
    `assigned_by` int(11) DEFAULT NULL,
    `assigned_to` int(11) DEFAULT NULL,
    `is_self_created` tinyint(1) DEFAULT 1,
    `estimated_minutes` int(11) DEFAULT NULL,
    `actual_minutes` int(11) DEFAULT NULL,
    `started_at` datetime DEFAULT NULL,
    `completed_at` datetime DEFAULT NULL,
    `attendance_id` int(11) DEFAULT NULL,
    `requires_approval` tinyint(1) DEFAULT 0,
    `is_approved` tinyint(1) DEFAULT 1,
    `approved_by` int(11) DEFAULT NULL,
    `approved_at` datetime DEFAULT NULL,
    `tags` text,
    `completion_note` text,
    `deleted_at` datetime DEFAULT NULL,
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_daily_task_user_date` (`user_id`, `task_date`),
    KEY `idx_daily_task_status` (`status`),
    KEY `idx_daily_task_category` (`category`),
    KEY `idx_daily_task_assigned_to` (`assigned_to`),
    KEY `idx_daily_task_attendance` (`attendance_id`),
    KEY `idx_daily_task_deleted` (`deleted_at`),
    KEY `fk_daily_tasks_user` (`user_id`),
    KEY `fk_daily_tasks_assigned_by` (`assigned_by`),
    KEY `fk_daily_tasks_assigned_to` (`assigned_to`),
    KEY `fk_daily_tasks_approved_by` (`approved_by`),
    KEY `fk_daily_tasks_attendance` (`attendance_id`),
    CONSTRAINT `fk_daily_tasks_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_daily_tasks_assigned_by` FOREIGN KEY (`assigned_by`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_daily_tasks_assigned_to` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_daily_tasks_approved_by` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_daily_tasks_attendance` FOREIGN KEY (`attendance_id`) REFERENCES `attendance_records` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create task_attachments table
CREATE TABLE IF NOT EXISTS `task_attachments` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `task_id` int(11) NOT NULL,
    `filename` varchar(255) NOT NULL,
    `original_filename` varchar(255) NOT NULL,
    `file_type` varchar(50) NOT NULL,
    `file_size` int(11) NOT NULL,
    `base64_content` longtext NOT NULL,
    `uploaded_by` int(11) NOT NULL,
    `uploaded_at` datetime DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_task_attachment_task` (`task_id`),
    KEY `idx_task_attachment_uploader` (`uploaded_by`),
    KEY `idx_task_attachment_uploaded` (`uploaded_at`),
    KEY `fk_task_attachments_task` (`task_id`),
    KEY `fk_task_attachments_uploader` (`uploaded_by`),
    CONSTRAINT `fk_task_attachments_task` FOREIGN KEY (`task_id`) REFERENCES `daily_tasks` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_task_attachments_uploader` FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create task_comments table
CREATE TABLE IF NOT EXISTS `task_comments` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `task_id` int(11) NOT NULL,
    `user_id` int(11) NOT NULL,
    `comment_text` text NOT NULL,
    `is_system_comment` tinyint(1) DEFAULT 0,
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_task_comment_task` (`task_id`),
    KEY `idx_task_comment_user` (`user_id`),
    KEY `idx_task_comment_created` (`created_at`),
    KEY `fk_task_comments_task` (`task_id`),
    KEY `fk_task_comments_user` (`user_id`),
    CONSTRAINT `fk_task_comments_task` FOREIGN KEY (`task_id`) REFERENCES `daily_tasks` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_task_comments_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create task_settings table
CREATE TABLE IF NOT EXISTS `task_settings` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `company_id` varchar(100) DEFAULT 'PT. Kian Santang Muliatama',
    `require_task_before_clockout` tinyint(1) DEFAULT 1,
    `minimum_tasks_required` int(11) DEFAULT 1,
    `allow_self_task_creation` tinyint(1) DEFAULT 1,
    `max_attachment_size_mb` int(11) DEFAULT 5,
    `allowed_file_types` text,
    `notification_enabled` tinyint(1) DEFAULT 1,
    `email_notification_enabled` tinyint(1) DEFAULT 1,
    `default_task_category` varchar(20) DEFAULT 'regular',
    `default_task_priority` varchar(20) DEFAULT 'medium',
    `auto_approve_self_tasks` tinyint(1) DEFAULT 1,
    `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_task_settings_company` (`company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default task settings
INSERT INTO `task_settings` (
    `company_id`,
    `require_task_before_clockout`,
    `minimum_tasks_required`,
    `allow_self_task_creation`,
    `max_attachment_size_mb`,
    `allowed_file_types`,
    `notification_enabled`,
    `email_notification_enabled`,
    `default_task_category`,
    `default_task_priority`,
    `auto_approve_self_tasks`
) VALUES (
    'PT. Kian Santang Muliatama',
    1,
    1,
    1,
    5,
    '["jpg", "jpeg", "png", "pdf", "docx", "xlsx"]',
    1,
    1,
    'regular',
    'medium',
    1
) ON DUPLICATE KEY UPDATE
    `require_task_before_clockout` = VALUES(`require_task_before_clockout`),
    `minimum_tasks_required` = VALUES(`minimum_tasks_required`),
    `allow_self_task_creation` = VALUES(`allow_self_task_creation`),
    `max_attachment_size_mb` = VALUES(`max_attachment_size_mb`),
    `allowed_file_types` = VALUES(`allowed_file_types`),
    `notification_enabled` = VALUES(`notification_enabled`),
    `email_notification_enabled` = VALUES(`email_notification_enabled`),
    `default_task_category` = VALUES(`default_task_category`),
    `default_task_priority` = VALUES(`default_task_priority`),
    `auto_approve_self_tasks` = VALUES(`auto_approve_self_tasks`);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS `idx_daily_tasks_created_at` ON `daily_tasks` (`created_at`);
CREATE INDEX IF NOT EXISTS `idx_daily_tasks_updated_at` ON `daily_tasks` (`updated_at`);
CREATE INDEX IF NOT EXISTS `idx_daily_tasks_priority` ON `daily_tasks` (`priority`);
CREATE INDEX IF NOT EXISTS `idx_daily_tasks_started_at` ON `daily_tasks` (`started_at`);
CREATE INDEX IF NOT EXISTS `idx_daily_tasks_completed_at` ON `daily_tasks` (`completed_at`);

-- Add composite indexes for common queries
CREATE INDEX IF NOT EXISTS `idx_daily_tasks_user_status` ON `daily_tasks` (`user_id`, `status`);
CREATE INDEX IF NOT EXISTS `idx_daily_tasks_date_status` ON `daily_tasks` (`task_date`, `status`);
CREATE INDEX IF NOT EXISTS `idx_daily_tasks_assigned_status` ON `daily_tasks` (`assigned_to`, `status`);

-- Add indexes for task_attachments
CREATE INDEX IF NOT EXISTS `idx_task_attachments_file_type` ON `task_attachments` (`file_type`);
CREATE INDEX IF NOT EXISTS `idx_task_attachments_file_size` ON `task_attachments` (`file_size`);

-- Add indexes for task_comments
CREATE INDEX IF NOT EXISTS `idx_task_comments_system` ON `task_comments` (`is_system_comment`);
CREATE INDEX IF NOT EXISTS `idx_task_comments_updated` ON `task_comments` (`updated_at`);

-- Migration completed successfully
SELECT 'Daily Task tables created successfully' as status;
