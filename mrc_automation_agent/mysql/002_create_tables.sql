USE `webagent`;

CREATE TABLE IF NOT EXISTS `mrc_automation_settings` (
    `id` TINYINT UNSIGNED NOT NULL,
    `enabled` BOOLEAN NOT NULL DEFAULT FALSE,
    `timezone` VARCHAR(64) NOT NULL DEFAULT 'UTC',
    `updated_at` TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (`id`),
    CONSTRAINT `chk_mrc_automation_settings_singleton` CHECK (`id` = 1)
) ENGINE=InnoDB;

INSERT INTO `mrc_automation_settings` (`id`, `enabled`)
VALUES (1, FALSE)
ON DUPLICATE KEY UPDATE `id` = VALUES(`id`);

CREATE TABLE IF NOT EXISTS `mrc_reporting_cycles` (
    `cycle_code` VARCHAR(10) NOT NULL,
    `latest_scan_id` BIGINT UNSIGNED NULL,
    `created_at` TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (`cycle_code`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `mrc_scan_runs` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `cycle_code` VARCHAR(10) NOT NULL,
    `status` ENUM('queued', 'running', 'succeeded', 'failed') NOT NULL,
    `triggered_by` ENUM('manual', 'scheduler') NOT NULL,
    `started_at` TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `completed_at` TIMESTAMP(6) NULL,
    `files_found` INT UNSIGNED NOT NULL DEFAULT 0,
    `owners_found` INT UNSIGNED NOT NULL DEFAULT 0,
    `missing_comments` INT UNSIGNED NOT NULL DEFAULT 0,
    `error_message` TEXT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_mrc_scan_runs_cycle_status_completed` (`cycle_code`, `status`, `completed_at`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `mrc_scan_workbooks` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `cycle_code` VARCHAR(10) NOT NULL,
    `workbook_name` VARCHAR(255) NOT NULL,
    `workbook_url` TEXT NOT NULL,
    `latest_scan_run_id` BIGINT UNSIGNED NOT NULL,
    `modified_time` VARCHAR(64) NULL,
    `created_at` TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_mrc_scan_workbook_cycle_name` (`cycle_code`, `workbook_name`),
    KEY `idx_mrc_scan_workbooks_latest_run` (`latest_scan_run_id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `mrc_scan_items` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `scan_run_id` BIGINT UNSIGNED NOT NULL,
    `workbook_name` VARCHAR(255) NOT NULL,
    `workbook_url` TEXT NOT NULL,
    `sheet_name` VARCHAR(255) NOT NULL,
    `source_row` INT UNSIGNED NOT NULL,
    `function_team` VARCHAR(255) NULL,
    `project_name` VARCHAR(500) NOT NULL,
    `owner_name` VARCHAR(255) NULL,
    `owner_email` VARCHAR(320) NULL,
    `status_comments` TEXT NULL,
    `created_at` TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_mrc_scan_item_source` (`scan_run_id`, `workbook_name`, `sheet_name`, `source_row`),
    KEY `idx_mrc_scan_items_owner` (`scan_run_id`, `owner_email`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `mrc_email_deliveries` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `cycle_code` VARCHAR(10) NOT NULL,
    `scan_run_id` BIGINT UNSIGNED NOT NULL,
    `owner_email` VARCHAR(320) NOT NULL,
    `reminder_type` ENUM('reminder', 'lastreminder', 'ppt') NOT NULL,
    `status` ENUM('draft', 'sending', 'sent', 'failed') NOT NULL DEFAULT 'draft',
    `subject` VARCHAR(998) NOT NULL,
    `body_html` MEDIUMTEXT NOT NULL,
    `idempotency_key` VARCHAR(500) NOT NULL,
    `provider_message_id` VARCHAR(255) NULL,
    `sent_at` TIMESTAMP(6) NULL,
    `error_message` TEXT NULL,
    `created_at` TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_mrc_email_deliveries_idempotency` (`idempotency_key`),
    KEY `idx_mrc_email_deliveries_cycle_status` (`cycle_code`, `status`),
    KEY `idx_mrc_email_deliveries_run` (`scan_run_id`)
) ENGINE=InnoDB;
