-- HEI FastAPI SnailJob seed: independent namespace + group + Python jobs
-- namespace unique_id: a8c3e5f17b924d6e9f0a1b2c3d4e5f60 (NOT hei-boot Default)
-- group: hei_fastapi_admin / token: SJ_heiFastapiAdminToken1234567890ab
-- executor_type=2 means Python (Java client uses 1)
-- Console password set to admin/123456 (SHA256(MD5('123456'))) when admin row exists.

UPDATE sj_system_user
SET password = 'cdf4a007e2b02a0c49fc9b7ccfbb8a10c644f635e1765dcf2a7ab794ddc7edac',
    update_dt = now()
WHERE username = 'admin';

INSERT INTO sj_namespace (name, unique_id, description, create_dt, update_dt, deleted)
SELECT
    'hei-fastapi',
    'a8c3e5f17b924d6e9f0a1b2c3d4e5f60',
    'HEI FastAPI isolated namespace',
    now(),
    now(),
    0
WHERE NOT EXISTS (
    SELECT 1 FROM sj_namespace
    WHERE unique_id = 'a8c3e5f17b924d6e9f0a1b2c3d4e5f60'
);

INSERT INTO sj_group_config (
    namespace_id, group_name, description, token, group_status, version,
    group_partition, id_generator_mode, init_scene, create_dt, update_dt
)
SELECT
    'a8c3e5f17b924d6e9f0a1b2c3d4e5f60',
    'hei_fastapi_admin',
    'HEI FastAPI Python executor group',
    'SJ_heiFastapiAdminToken1234567890ab',
    1,
    1,
    0,
    1,
    1,
    now(),
    now()
WHERE NOT EXISTS (
    SELECT 1 FROM sj_group_config
    WHERE namespace_id = 'a8c3e5f17b924d6e9f0a1b2c3d4e5f60'
      AND group_name = 'hei_fastapi_admin'
);

-- trigger_type=1 CRON; job_status=1 enabled; task_type=1 cluster; route_key=4; executor_type=2 Python
INSERT INTO sj_job (
    namespace_id, biz_id, group_name, job_name, args_str, args_type,
    next_trigger_at, job_status, task_type, route_key, executor_type, executor_info,
    trigger_type, trigger_interval, block_strategy, executor_timeout, max_retry_times,
    parallel_num, retry_interval, bucket_index, resident, notify_ids, description, deleted,
    create_dt, update_dt
)
SELECT
    'a8c3e5f17b924d6e9f0a1b2c3d4e5f60',
    'hei-fastapi-accountPurgeCancelledAccounts',
    'hei_fastapi_admin',
    '清理超期已注销账号',
    '15',
    1,
    (EXTRACT(EPOCH FROM now()) * 1000)::bigint,
    1, 1, 4, 2, 'accountPurgeCancelledAccounts',
    1, '0 0 3 * * ?', 1, 0, 0,
    1, 0, 0, 0, '', 'Purge cancelled accounts past retention', 0,
    now(), now()
WHERE NOT EXISTS (
    SELECT 1 FROM sj_job
    WHERE namespace_id = 'a8c3e5f17b924d6e9f0a1b2c3d4e5f60'
      AND biz_id = 'hei-fastapi-accountPurgeCancelledAccounts'
);

INSERT INTO sj_job (
    namespace_id, biz_id, group_name, job_name, args_str, args_type,
    next_trigger_at, job_status, task_type, route_key, executor_type, executor_info,
    trigger_type, trigger_interval, block_strategy, executor_timeout, max_retry_times,
    parallel_num, retry_interval, bucket_index, resident, notify_ids, description, deleted,
    create_dt, update_dt
)
SELECT
    'a8c3e5f17b924d6e9f0a1b2c3d4e5f60',
    'hei-fastapi-bannerFlushInteractions',
    'hei_fastapi_admin',
    '刷写 Banner 交互增量',
    NULL,
    1,
    (EXTRACT(EPOCH FROM now()) * 1000)::bigint,
    1, 1, 4, 2, 'bannerFlushInteractions',
    1, '0 */5 * * * ?', 1, 0, 0,
    1, 0, 0, 0, '', 'Flush banner interaction deltas from Redis to DB', 0,
    now(), now()
WHERE NOT EXISTS (
    SELECT 1 FROM sj_job
    WHERE namespace_id = 'a8c3e5f17b924d6e9f0a1b2c3d4e5f60'
      AND biz_id = 'hei-fastapi-bannerFlushInteractions'
);

INSERT INTO sj_job (
    namespace_id, biz_id, group_name, job_name, args_str, args_type,
    next_trigger_at, job_status, task_type, route_key, executor_type, executor_info,
    trigger_type, trigger_interval, block_strategy, executor_timeout, max_retry_times,
    parallel_num, retry_interval, bucket_index, resident, notify_ids, description, deleted,
    create_dt, update_dt
)
SELECT
    'a8c3e5f17b924d6e9f0a1b2c3d4e5f60',
    'hei-fastapi-bannerStatusJob',
    'hei_fastapi_admin',
    '同步 Banner 状态',
    NULL,
    1,
    (EXTRACT(EPOCH FROM now()) * 1000)::bigint,
    1, 1, 4, 2, 'bannerStatusJob',
    1, '0 */5 * * * ?', 1, 0, 0,
    1, 0, 0, 0, '', 'Sync banner ENABLED/DISABLED by start_at/end_at', 0,
    now(), now()
WHERE NOT EXISTS (
    SELECT 1 FROM sj_job
    WHERE namespace_id = 'a8c3e5f17b924d6e9f0a1b2c3d4e5f60'
      AND biz_id = 'hei-fastapi-bannerStatusJob'
);

INSERT INTO sj_job (
    namespace_id, biz_id, group_name, job_name, args_str, args_type,
    next_trigger_at, job_status, task_type, route_key, executor_type, executor_info,
    trigger_type, trigger_interval, block_strategy, executor_timeout, max_retry_times,
    parallel_num, retry_interval, bucket_index, resident, notify_ids, description, deleted,
    create_dt, update_dt
)
SELECT
    'a8c3e5f17b924d6e9f0a1b2c3d4e5f60',
    'hei-fastapi-auditAnalysisCycle',
    'hei_fastapi_admin',
    '审计告警分析',
    NULL,
    1,
    (EXTRACT(EPOCH FROM now()) * 1000)::bigint,
    1, 1, 4, 2, 'auditAnalysisCycle',
    1, '0 */5 * * * ?', 1, 0, 0,
    1, 0, 0, 0, '', 'Audit alert analysis cycle', 0,
    now(), now()
WHERE NOT EXISTS (
    SELECT 1 FROM sj_job
    WHERE namespace_id = 'a8c3e5f17b924d6e9f0a1b2c3d4e5f60'
      AND biz_id = 'hei-fastapi-auditAnalysisCycle'
);

INSERT INTO sj_job (
    namespace_id, biz_id, group_name, job_name, args_str, args_type,
    next_trigger_at, job_status, task_type, route_key, executor_type, executor_info,
    trigger_type, trigger_interval, block_strategy, executor_timeout, max_retry_times,
    parallel_num, retry_interval, bucket_index, resident, notify_ids, description, deleted,
    create_dt, update_dt
)
SELECT
    'a8c3e5f17b924d6e9f0a1b2c3d4e5f60',
    'hei-fastapi-sysFileCleanupLocalOrphans',
    'hei_fastapi_admin',
    '清理本地存储孤儿文件',
    NULL,
    1,
    (EXTRACT(EPOCH FROM now()) * 1000)::bigint,
    1, 1, 4, 2, 'sysFileCleanupLocalOrphans',
    1, '0 0 * * * ?', 1, 0, 0,
    1, 0, 0, 0, '', 'Cleanup local storage orphans older than min age', 0,
    now(), now()
WHERE NOT EXISTS (
    SELECT 1 FROM sj_job
    WHERE namespace_id = 'a8c3e5f17b924d6e9f0a1b2c3d4e5f60'
      AND biz_id = 'hei-fastapi-sysFileCleanupLocalOrphans'
);
