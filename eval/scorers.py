"""Custom scorers for evaluating the NBA analytics agent."""

import re


def data_eval(output, expected) -> float:
    """Check if expected numeric and string values appear in the agent output.

    For numeric values: checks if the number appears in the output text (1% tolerance).
    For string values: case-insensitive containment check.
    Returns the fraction of expected values found (0.0–1.0).
    """
    if not output or not expected:
        return 0.0

    response_text = output.get("response", "") if isinstance(output, dict) else str(output)

    # Extract all numbers from the response
    numbers_in_output = [float(n) for n in re.findall(r"[\d,]+\.?\d*", response_text.replace(",", ""))]

    total_checks = 0
    matches = 0

    # Check numeric values
    for expected_val in expected.get("values", []):
        total_checks += 1
        tolerance = abs(expected_val) * 0.01  # 1% tolerance
        for out_num in numbers_in_output:
            if abs(out_num - expected_val) <= tolerance:
                matches += 1
                break

    # Check string values
    response_lower = response_text.lower()
    for expected_str in expected.get("strings", []):
        total_checks += 1
        if expected_str.lower() in response_lower:
            matches += 1

    return matches / total_checks if total_checks > 0 else 0.0


def sql_eval(output, expected, metadata=None) -> float:
    """Compare agent's SQL to the reference by checking structural similarity.

    Checks: correct tables, correct date ranges, aggregation functions, GROUP BY presence.
    Returns structural similarity score (0.0–1.0).
    """
    if not output or not metadata:
        return 0.0

    agent_sql = output.get("sql_query", "") if isinstance(output, dict) else ""
    ref_sql = metadata.get("sql_query", "")

    if not agent_sql or not ref_sql:
        return 0.0

    agent_sql_upper = agent_sql.upper()
    ref_sql_upper = ref_sql.upper()

    checks = 0
    matches = 0

    # Check tables used
    table_names = ["PLAYER_GAME_STATS", "TEAM_GAME_STATS", "GAMES", "PLAYERS", "TEAMS", "ROSTERS"]
    for table in table_names:
        if table in ref_sql_upper:
            checks += 1
            if table in agent_sql_upper:
                matches += 1

    # Check date ranges
    date_pattern = r"\d{4}-\d{2}-\d{2}"
    ref_dates = set(re.findall(date_pattern, ref_sql))
    if ref_dates:
        agent_dates = set(re.findall(date_pattern, agent_sql))
        for d in ref_dates:
            checks += 1
            if d in agent_dates:
                matches += 1

    # Check aggregation functions
    agg_functions = ["SUM", "AVG", "COUNT", "MIN", "MAX"]
    for func in agg_functions:
        if func + "(" in ref_sql_upper:
            checks += 1
            if func + "(" in agent_sql_upper:
                matches += 1

    # Check GROUP BY
    if "GROUP BY" in ref_sql_upper:
        checks += 1
        if "GROUP BY" in agent_sql_upper:
            matches += 1

    return matches / checks if checks > 0 else 0.0
