#!/usr/bin/env python3
"""Query Copilot CLI session store and output JSON for the journal skill."""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: query-sessions.py <from_iso> <to_iso>", file=sys.stderr)
        sys.exit(1)

    from_iso = sys.argv[1]
    to_iso = sys.argv[2]
    db_path = Path.home() / ".copilot" / "session-store.db"

    if not db_path.exists():
        print(
            f"Session store not found at {db_path}. Has Copilot CLI been run before?",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate date args using SQLite's own parser
    with sqlite3.connect(":memory:") as _vc:
        row = _vc.execute("SELECT datetime(?), datetime(?)", (from_iso, to_iso)).fetchone()
        if row[0] is None or row[1] is None:
            print(f"Invalid date format. Use YYYY-MM-DDTHH:MM:SS (got: {from_iso!r}, {to_iso!r})", file=sys.stderr)
            sys.exit(1)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        sessions = conn.execute(
            """
            SELECT id, repository, branch, summary, created_at, updated_at
            FROM sessions
            WHERE datetime(created_at) >= datetime(?)
              AND datetime(created_at) <= datetime(?)
            ORDER BY created_at
            """,
            (from_iso, to_iso),
        ).fetchall()

        output: dict[str, Any] = {
            "timeframe": {"from": from_iso, "to": to_iso},
            "sessions": [],
        }

        for session in sessions:
            session_id = session["id"]

            turn_count = conn.execute(
                "SELECT COUNT(*) FROM turns WHERE session_id = ?",
                (session_id,),
            ).fetchone()[0]

            checkpoints = conn.execute(
                """
                SELECT title, overview, work_done, technical_details, important_files, next_steps
                FROM checkpoints
                WHERE session_id = ?
                ORDER BY checkpoint_number
                """,
                (session_id,),
            ).fetchall()

            # Determine if there is any useful checkpoint content
            def _has_text(*values: Any) -> bool:
                return any(v for v in values if isinstance(v, str) and v.strip())

            checkpoints_have_content = any(
                _has_text(c["overview"], c["work_done"], c["technical_details"])
                for c in checkpoints
            )

            # Skip sessions with nothing to say
            if turn_count == 0 and not (session["summary"] or "").strip() and not checkpoints_have_content:
                continue

            if not checkpoints:
                checkpoints_data: list[dict[str, Any]] = [
                    {
                        "title": "",
                        "overview": session["summary"] or "",
                        "work_done": "",
                        "technical_details": "",
                        "important_files": "",
                        "next_steps": "",
                    }
                ]
            else:
                checkpoints_data = [dict(c) for c in checkpoints]

            # Always include the full conversation so the sub-agent can build
            # a complete narrative, falling back to turns when checkpoints lack content.
            turns_data: list[dict[str, Any]] = []
            if turn_count > 0:
                turns = conn.execute(
                    """
                    SELECT turn_index, user_message, assistant_response
                    FROM turns
                    WHERE session_id = ?
                    ORDER BY turn_index
                    """,
                    (session_id,),
                ).fetchall()
                for t in turns:
                    user_msg = (t["user_message"] or "").strip()
                    asst_msg = (t["assistant_response"] or "").strip()
                    # Skip skill-context injection turns, empty turns, and
                    # turns that invoke the session-journal skill itself
                    # (invocation may appear anywhere in the message, e.g. as a
                    # slash command or via the skill tool wrapper)
                    if user_msg.startswith("<skill-context") or user_msg.startswith("<system_reminder"):
                        continue
                    if "session-journal" in user_msg.lower():
                        continue
                    turns_data.append(
                        {
                            "index": t["turn_index"],
                            "user": user_msg,
                            "assistant": asst_msg,
                        }
                    )

            refs = conn.execute(
                "SELECT ref_type, ref_value FROM session_refs WHERE session_id = ?",
                (session_id,),
            ).fetchall()

            files = conn.execute(
                "SELECT file_path, tool_name FROM session_files WHERE session_id = ?",
                (session_id,),
            ).fetchall()

            output["sessions"].append(
                {
                    "id": session_id,
                    "repository": session["repository"] or "",
                    "branch": session["branch"] or "",
                    "summary": session["summary"] or "",
                    "created_at": session["created_at"],
                    "updated_at": session["updated_at"],
                    "checkpoints": checkpoints_data,
                    "turns": turns_data,
                    "refs": [dict(r) for r in refs],
                    "files": [dict(f) for f in files],
                }
            )

        conn.close()
        print(json.dumps(output, indent=2))
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
