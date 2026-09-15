USE `webagent`;

ALTER TABLE `mrc_email_deliveries`
    MODIFY COLUMN `reminder_type`
        ENUM('manual', 'tuesday', 'thursday', 'monday', 'reminder', 'lastreminder', 'ppt')
        NOT NULL;

UPDATE `mrc_email_deliveries`
SET `reminder_type` = CASE
    WHEN `reminder_type` IN ('manual', 'tuesday', 'thursday') THEN 'reminder'
    WHEN `reminder_type` = 'monday' THEN 'lastreminder'
    ELSE `reminder_type`
END,
    `idempotency_key` = REPLACE(
        REPLACE(
            REPLACE(
                REPLACE(`idempotency_key`, ':manual:', ':reminder:'),
                ':tuesday:', ':reminder:'
            ),
            ':thursday:', ':reminder:'
        ),
        ':monday:', ':lastreminder:'
    );

ALTER TABLE `mrc_email_deliveries`
    MODIFY COLUMN `reminder_type`
        ENUM('reminder', 'lastreminder', 'ppt') NOT NULL;