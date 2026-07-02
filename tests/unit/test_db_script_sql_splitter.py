from scripts.db import filtered_validation_rows, split_sql_statements


def test_split_sql_statements_handles_dollar_quoted_blocks() -> None:
    sql = """
    CREATE TABLE example(id int);
    DO $$
    BEGIN
      RAISE NOTICE 'hello; still inside block';
    END $$;
    SELECT 1;
    """

    statements = split_sql_statements(sql)

    assert len(statements) == 3
    assert statements[1].startswith("DO $$")


def test_validation_filter_allows_known_global_and_partition_rows() -> None:
    assert filtered_validation_rows(1, [("analytics", "metric_definitions")]) == []
    assert filtered_validation_rows(
        4,
        [
            (
                "platform",
                "audit_logs_default",
                "before_state",
                "NOT ALLOWED - normalize or add approved exception",
            )
        ],
    ) == []
    assert filtered_validation_rows(5, [("pg_catalog", "pg_class", "relacl", "NOT ALLOWED")]) == []
    assert filtered_validation_rows(7, [("fk_example", "tenant.example")]) == []
