USE `webagent`;

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