from __future__ import annotations

from .models import TaskSubmission, TaskType


SCENARIOS: dict[str, dict] = {
    "sql-collapse": {
        "description": "Three differently formatted but equivalent sales queries collapse into one SEU.",
        "tasks": [
            {"delay_ms": 0, "task": TaskSubmission(agent_id="Agent A", task_type=TaskType.SQL_QUERY, payload="SELECT customer_id, SUM(amount) AS total FROM transactions WHERE DATE(created_at) >= '2024-01-01' AND region = 'West' GROUP BY customer_id;")},
            {"delay_ms": 140, "task": TaskSubmission(agent_id="Agent B", task_type=TaskType.SQL_QUERY, payload="select CUSTOMER_ID, sum(AMOUNT) total from TRANSACTIONS t where t.region = 'West' and date(t.created_at) >= '2024-01-01' group by CUSTOMER_ID;")},
            {"delay_ms": 280, "task": TaskSubmission(agent_id="Agent C", task_type=TaskType.SQL_QUERY, payload="SELECT c_id, SUM(amt) FROM txns WHERE txns.region='West' AND DATE(txns.created_at) >= '2024-01-01' GROUP BY c_id;")},
        ],
    },
    "nl-collapse": {
        "description": "Three support-ticket retrieval requests collapse by semantic similarity within the admission window.",
        "tasks": [
            {"delay_ms": 0, "task": TaskSubmission(agent_id="Agent A", task_type=TaskType.NATURAL_LANGUAGE, payload="Get me all open support tickets assigned to the enterprise tier from last week with their resolution status.")},
            {"delay_ms": 180, "task": TaskSubmission(agent_id="Agent B", task_type=TaskType.NATURAL_LANGUAGE, payload="Retrieve enterprise support cases opened in the past 7 days that are still unresolved or in progress.")},
            {"delay_ms": 320, "task": TaskSubmission(agent_id="Agent C", task_type=TaskType.NATURAL_LANGUAGE, payload="List unresolved enterprise customer tickets from the last week including current status.")},
        ],
    },
    "unique-task": {
        "description": "A distinct request remains unique and executes without collapse.",
        "tasks": [
            {"delay_ms": 0, "task": TaskSubmission(agent_id="Agent A", task_type=TaskType.NATURAL_LANGUAGE, payload="Summarize all contracts expiring next quarter for the procurement team.")},
        ],
    },
}
