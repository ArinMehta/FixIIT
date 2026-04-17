-- Ticket shard audit triggers.
-- Logic:
-- - If app sets @app_actor_member_id and @app_endpoint in the same connection:
--     source = 'API'
-- - Otherwise:
--     source = 'DIRECT_DB'

DROP TRIGGER IF EXISTS trg_tickets_ai_audit;
DROP TRIGGER IF EXISTS trg_tickets_au_audit;
DROP TRIGGER IF EXISTS trg_tickets_ad_audit;

DELIMITER $$

CREATE TRIGGER trg_tickets_ai_audit
AFTER INSERT ON tickets
FOR EACH ROW
BEGIN
    INSERT INTO db_change_audit (
        table_name, operation, pk_value, actor_member_id, endpoint, source,
        before_json, after_json, changed_at
    )
    VALUES (
        'tickets',
        'INSERT',
        CAST(NEW.ticket_id AS CHAR),
        @app_actor_member_id,
        @app_endpoint,
        CASE WHEN @app_actor_member_id IS NULL OR @app_endpoint IS NULL THEN 'DIRECT_DB' ELSE 'API' END,
        NULL,
        JSON_OBJECT(
            'ticket_id', NEW.ticket_id,
            'title', NEW.title,
            'description', NEW.description,
            'member_id', NEW.member_id,
            'location_id', NEW.location_id,
            'category_id', NEW.category_id,
            'priority', NEW.priority,
            'status_id', NEW.status_id,
            'created_at', NEW.created_at,
            'updated_at', NEW.updated_at
        ),
        NOW()
    );
END$$

CREATE TRIGGER trg_tickets_au_audit
AFTER UPDATE ON tickets
FOR EACH ROW
BEGIN
    INSERT INTO db_change_audit (
        table_name, operation, pk_value, actor_member_id, endpoint, source,
        before_json, after_json, changed_at
    )
    VALUES (
        'tickets',
        'UPDATE',
        CAST(NEW.ticket_id AS CHAR),
        @app_actor_member_id,
        @app_endpoint,
        CASE WHEN @app_actor_member_id IS NULL OR @app_endpoint IS NULL THEN 'DIRECT_DB' ELSE 'API' END,
        JSON_OBJECT(
            'ticket_id', OLD.ticket_id,
            'title', OLD.title,
            'description', OLD.description,
            'member_id', OLD.member_id,
            'location_id', OLD.location_id,
            'category_id', OLD.category_id,
            'priority', OLD.priority,
            'status_id', OLD.status_id,
            'created_at', OLD.created_at,
            'updated_at', OLD.updated_at
        ),
        JSON_OBJECT(
            'ticket_id', NEW.ticket_id,
            'title', NEW.title,
            'description', NEW.description,
            'member_id', NEW.member_id,
            'location_id', NEW.location_id,
            'category_id', NEW.category_id,
            'priority', NEW.priority,
            'status_id', NEW.status_id,
            'created_at', NEW.created_at,
            'updated_at', NEW.updated_at
        ),
        NOW()
    );
END$$

CREATE TRIGGER trg_tickets_ad_audit
AFTER DELETE ON tickets
FOR EACH ROW
BEGIN
    INSERT INTO db_change_audit (
        table_name, operation, pk_value, actor_member_id, endpoint, source,
        before_json, after_json, changed_at
    )
    VALUES (
        'tickets',
        'DELETE',
        CAST(OLD.ticket_id AS CHAR),
        @app_actor_member_id,
        @app_endpoint,
        CASE WHEN @app_actor_member_id IS NULL OR @app_endpoint IS NULL THEN 'DIRECT_DB' ELSE 'API' END,
        JSON_OBJECT(
            'ticket_id', OLD.ticket_id,
            'title', OLD.title,
            'description', OLD.description,
            'member_id', OLD.member_id,
            'location_id', OLD.location_id,
            'category_id', OLD.category_id,
            'priority', OLD.priority,
            'status_id', OLD.status_id,
            'created_at', OLD.created_at,
            'updated_at', OLD.updated_at
        ),
        NULL,
        NOW()
    );
END$$

DELIMITER ;
