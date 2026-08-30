"""
EvolvixOS Instinct System v1.0
Adapted from ECC Continuous Learning v2.1 — MIT licensed (affaan-m/ECC)

Instincts are small atomic learned behaviors with confidence scoring.
They persist across sessions and evolve into skills/commands/agents.

Storage: SQLite (evolvixos_instincts.db)
Scope: project-scoped + global (project instincts promoted after 2+ projects)

Instinct model:
  id: unique identifier
  trigger: "when writing new functions"
  action: "use functional patterns over classes"
  confidence: 0.3-0.9 (tentative → near certain)
  domain: code-style, testing, git, debugging, workflow, security, etc.
  evidence: list of observations that created/validated it
  scope: project | global
  project_id: hash of project (or "global")
  created_date: ISO timestamp
  last_seen: ISO timestamp
  occurrence_count: how many times observed
"""

import json
import sqlite3
import hashlib
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from contextlib import contextmanager

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

DB_PATH = os.environ.get(
    "EVOLVIX_INSTINCT_DB",
    str(Path(__file__).parent / "evolvixos_instincts.db")
)

CONFIDENCE_MIN = 0.3
CONFIDENCE_MAX = 0.9
CONFIDENCE_BOOST = 0.05  # per observation
PROMOTION_THRESHOLD = 2   # projects before global promotion
PRUNE_TTL_DAYS = 30       # pending instincts older than this get pruned


@dataclass
class Instinct:
    id: str
    trigger: str
    action: str
    confidence: float
    domain: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    scope: str = "project"  # project | global
    project_id: str = "global"
    project_name: str = ""
    created_date: str = ""
    last_seen: str = ""
    occurrence_count: int = 0
    status: str = "pending"  # pending | active | evolved | pruned

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Instinct":
        return cls(
            id=row["id"],
            trigger=row["trigger"],
            action=row["action"],
            confidence=row["confidence"],
            domain=row["domain"],
            evidence=json.loads(row["evidence"]) if row["evidence"] else [],
            scope=row["scope"],
            project_id=row["project_id"],
            project_name=row["project_name"],
            created_date=row["created_date"],
            last_seen=row["last_seen"],
            occurrence_count=row["occurrence_count"],
            status=row["status"],
        )


# ─────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────

def _get_db() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    """Initialize the instinct database."""
    with _get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS instincts (
                id TEXT PRIMARY KEY,
                trigger TEXT NOT NULL,
                action TEXT NOT NULL,
                confidence REAL NOT NULL,
                domain TEXT NOT NULL,
                evidence TEXT DEFAULT '[]',
                scope TEXT DEFAULT 'project',
                project_id TEXT DEFAULT 'global',
                project_name TEXT DEFAULT '',
                created_date TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                occurrence_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending'
            )
        """)
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_domain ON instincts(domain)
        """)
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_scope_project ON instincts(scope, project_id)
        """)
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON instincts(status)
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS project_registry (
                project_id TEXT PRIMARY KEY,
                project_name TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                instinct_count INTEGER DEFAULT 0
            )
        """)
        db.commit()


# ─────────────────────────────────────────────
# Project Detection
# ─────────────────────────────────────────────

def detect_project(project_path: str = "", project_name: str = "") -> Dict[str, str]:
    """Detect project context from path or git remote."""
    if not project_path:
        project_path = os.getcwd()

    # Try git remote URL
    try:
        import subprocess
        result = subprocess.run(
            ["git", "-C", project_path, "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0 and result.stdout.strip():
            remote = result.stdout.strip()
            # Strip credentials
            remote = re.sub(r"://[^@]+@", "://", remote)
            pid = hashlib.sha256(remote.encode()).hexdigest()[:12]
            pname = remote.split("/")[-1].replace(".git", "")
            return {"id": pid, "name": pname, "root": project_path}
    except Exception:
        pass

    # Fallback: hash the path
    pid = hashlib.sha256(project_path.encode()).hexdigest()[:12]
    pname = project_name or Path(project_path).name or "unknown"
    return {"id": pid, "name": pname, "root": project_path}


# ─────────────────────────────────────────────
# Instinct Operations
# ─────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _instinct_id(trigger: str, action: str, project_id: str) -> str:
    raw = f"{trigger}|{action}|{project_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def add_instinct(
    trigger: str,
    action: str,
    domain: str,
    confidence: float = CONFIDENCE_MIN,
    evidence: Optional[Dict[str, Any]] = None,
    project_id: str = "global",
    project_name: str = "",
) -> Dict[str, Any]:
    """Add or update an instinct. Returns the instinct state."""
    init_db()
    iid = _instinct_id(trigger, action, project_id)
    now = _now()

    evidence_list = []
    if evidence:
        evidence_list = [evidence] if isinstance(evidence, dict) else evidence

    with _get_db() as db:
        existing = db.execute(
            "SELECT * FROM instincts WHERE id = ?", (iid,)
        ).fetchone()

        if existing:
            # Boost confidence
            new_confidence = min(
                existing["confidence"] + CONFIDENCE_BOOST,
                CONFIDENCE_MAX
            )
            # Append evidence
            old_evidence = json.loads(existing["evidence"]) if existing["evidence"] else []
            old_evidence.extend(evidence_list)
            # Keep last 10 evidence items
            old_evidence = old_evidence[-10:]

            db.execute("""
                UPDATE instincts
                SET confidence = ?, last_seen = ?, occurrence_count = ?,
                    evidence = ?, status = 'active'
                WHERE id = ?
            """, (
                new_confidence,
                now,
                existing["occurrence_count"] + 1,
                json.dumps(old_evidence),
                iid
            ))
            db.commit()
            return {"id": iid, "action": "updated", "confidence": new_confidence}
        else:
            inst = Instinct(
                id=iid,
                trigger=trigger,
                action=action,
                confidence=confidence,
                domain=domain,
                evidence=evidence_list,
                project_id=project_id,
                project_name=project_name,
                created_date=now,
                last_seen=now,
                occurrence_count=1,
                status="pending",
            )
            db.execute("""
                INSERT INTO instincts
                (id, trigger, action, confidence, domain, evidence, scope,
                 project_id, project_name, created_date, last_seen,
                 occurrence_count, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inst.id, inst.trigger, inst.action, inst.confidence,
                inst.domain, json.dumps(inst.evidence), inst.scope,
                inst.project_id, inst.project_name, inst.created_date,
                inst.last_seen, inst.occurrence_count, inst.status
            ))
            # Update project registry
            db.execute("""
                INSERT OR IGNORE INTO project_registry
                (project_id, project_name, first_seen, last_seen, instinct_count)
                VALUES (?, ?, ?, ?, 0)
            """, (project_id, project_name, now, now))
            db.execute("""
                UPDATE project_registry
                SET last_seen = ?, instinct_count = instinct_count + 1
                WHERE project_id = ?
            """, (now, project_id))
            db.commit()
            return {"id": iid, "action": "created", "confidence": confidence}


def get_instincts(
    domain: Optional[str] = None,
    project_id: Optional[str] = None,
    scope: Optional[str] = None,
    min_confidence: float = 0.0,
    status: str = "active",
) -> List[Dict[str, Any]]:
    """Retrieve instincts matching criteria."""
    init_db()
    query = "SELECT * FROM instincts WHERE confidence >= ?"
    params: list = [min_confidence]

    if domain:
        query += " AND domain = ?"
        params.append(domain)
    if project_id:
        query += " AND (project_id = ? OR scope = 'global')"
        params.append(project_id)
    if scope:
        query += " AND scope = ?"
        params.append(scope)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY confidence DESC, last_seen DESC"

    with _get_db() as db:
        rows = db.execute(query, params).fetchall()
        return [Instinct.from_row(r).to_dict() for r in rows]


def promote_instinct(instinct_id: str) -> Dict[str, Any]:
    """Promote a project instinct to global scope."""
    init_db()
    with _get_db() as db:
        row = db.execute(
            "SELECT * FROM instincts WHERE id = ?", (instinct_id,)
        ).fetchone()
        if not row:
            return {"error": "Instinct not found"}
        if row["scope"] == "global":
            return {"id": instinct_id, "action": "noop", "reason": "already global"}

        # Check if seen in 2+ projects (promotion threshold)
        similar = db.execute(
            "SELECT COUNT(DISTINCT project_id) as count FROM instincts "
            "WHERE trigger = ? AND action = ? AND scope = 'project'",
            (row["trigger"], row["action"])
        ).fetchone()
        if similar["count"] < PROMOTION_THRESHOLD:
            return {
                "id": instinct_id,
                "action": "rejected",
                "reason": f"Only seen in {similar['count']} project(s), need {PROMOTION_THRESHOLD}"
            }

        db.execute(
            "UPDATE instincts SET scope = 'global' WHERE id = ?",
            (instinct_id,)
        )
        db.commit()
        return {"id": instinct_id, "action": "promoted", "scope": "global"}


def evolve_instincts(domain: Optional[str] = None, project_id: Optional[str] = None) -> Dict[str, Any]:
    """Cluster related instincts and mark them as evolved into skills."""
    init_db()
    instincts = get_instincts(
        domain=domain,
        project_id=project_id,
        min_confidence=0.6,
        status="active",
    )
    if not instincts:
        return {"evolved": 0, "message": "No high-confidence instincts to evolve"}

    # Group by domain
    clusters: Dict[str, List[Dict]] = {}
    for inst in instincts:
        clusters.setdefault(inst["domain"], []).append(inst)

    evolved = 0
    with _get_db() as db:
        for domain_key, group in clusters.items():
            if len(group) >= 3:  # Need 3+ instincts to form a skill
                for inst in group:
                    db.execute(
                        "UPDATE instincts SET status = 'evolved' WHERE id = ?",
                        (inst["id"],)
                    )
                evolved += len(group)

        db.commit()

    return {
        "evolved": evolved,
        "clusters": {k: len(v) for k, v in clusters.items() if len(v) >= 3},
        "message": f"Evolved {evolved} instincts across {len(clusters)} domains"
    }


def prune_instincts(ttl_days: int = PRUNE_TTL_DAYS) -> Dict[str, Any]:
    """Delete pending instincts older than TTL."""
    init_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=ttl_days)).isoformat()
    with _get_db() as db:
        result = db.execute(
            "DELETE FROM instincts WHERE status = 'pending' AND last_seen < ?",
            (cutoff,)
        )
        db.commit()
        return {"pruned": result.rowcount, "ttl_days": ttl_days}


def export_instincts(
    domain: Optional[str] = None,
    project_id: Optional[str] = None,
    min_confidence: float = 0.5,
) -> str:
    """Export instincts as JSON for sharing."""
    instincts = get_instincts(
        domain=domain,
        project_id=project_id,
        min_confidence=min_confidence,
        status="",  # all statuses
    )
    return json.dumps({
        "version": "1.0",
        "exported": _now(),
        "count": len(instincts),
        "instincts": instincts,
    }, indent=2)


def import_instincts(json_str: str, target_project_id: str = "global") -> Dict[str, Any]:
    """Import instincts from JSON."""
    data = json.loads(json_str)
    imported = 0
    for inst_data in data.get("instincts", []):
        result = add_instinct(
            trigger=inst_data["trigger"],
            action=inst_data["action"],
            domain=inst_data["domain"],
            confidence=inst_data.get("confidence", CONFIDENCE_MIN),
            evidence=inst_data.get("evidence", []),
            project_id=target_project_id,
            project_name="imported",
        )
        if result.get("action") in ("created", "updated"):
            imported += 1
    return {"imported": imported, "total": len(data.get("instincts", []))}


def get_status() -> Dict[str, Any]:
    """Get overall instinct system status."""
    init_db()
    with _get_db() as db:
        total = db.execute("SELECT COUNT(*) as c FROM instincts").fetchone()["c"]
        active = db.execute("SELECT COUNT(*) as c FROM instincts WHERE status = 'active'").fetchone()["c"]
        pending = db.execute("SELECT COUNT(*) as c FROM instincts WHERE status = 'pending'").fetchone()["c"]
        evolved = db.execute("SELECT COUNT(*) as c FROM instincts WHERE status = 'evolved'").fetchone()["c"]
        global_count = db.execute("SELECT COUNT(*) as c FROM instincts WHERE scope = 'global'").fetchone()["c"]
        projects = db.execute("SELECT COUNT(*) as c FROM project_registry").fetchone()["c"]

        domains = db.execute(
            "SELECT domain, COUNT(*) as count FROM instincts GROUP BY domain ORDER BY count DESC"
        ).fetchall()

        avg_confidence = db.execute(
            "SELECT AVG(confidence) as avg FROM instincts WHERE status != 'pruned'"
        ).fetchone()["avg"] or 0.0

        return {
            "total": total,
            "active": active,
            "pending": pending,
            "evolved": evolved,
            "global": global_count,
            "projects": projects,
            "avg_confidence": round(avg_confidence, 3),
            "domains": {r["domain"]: r["count"] for r in domains},
        }


# ─────────────────────────────────────────────
# Observer Pattern — Detect patterns from tool calls
# ─────────────────────────────────────────────

class InstinctObserver:
    """
    Observes tool calls and detects patterns to create instincts.
    Adapted from ECC's observer agent pattern.

    Pattern types:
    1. User corrections: "No, use X instead of Y"
    2. Error resolutions: error followed by fix
    3. Repeated workflows: same tool sequence multiple times
    4. Tool preferences: consistent tool choice patterns
    """

    def __init__(self, project_id: str = "global", project_name: str = ""):
        self.project_id = project_id
        self.project_name = project_name
        self.observations: List[Dict] = []

    def record(self, event: str, tool: str, input_data: str = "", output_data: str = ""):
        """Record a tool call observation."""
        self.observations.append({
            "timestamp": _now(),
            "event": event,  # tool_start | tool_complete | user_message
            "tool": tool,
            "input": input_data[:500],
            "output": output_data[:500],
            "project_id": self.project_id,
        })

    def analyze(self) -> List[Dict[str, Any]]:
        """Analyze observations and create instincts."""
        created = []

        # Pattern 1: Error → Fix sequences
        for i, obs in enumerate(self.observations):
            if obs["event"] == "tool_complete" and "error" in obs.get("output", "").lower():
                # Look at next few tool calls for a fix
                for j in range(i + 1, min(i + 5, len(self.observations))):
                    next_obs = self.observations[j]
                    if next_obs["event"] == "tool_complete" and "error" not in next_obs.get("output", "").lower():
                        result = add_instinct(
                            trigger=f"when encountering error in {obs['tool']}",
                            action=f"try {next_obs['tool']} with adjusted parameters",
                            domain="error-recovery",
                            confidence=0.4,
                            evidence={"error": obs["output"][:200], "fix": next_obs["output"][:200]},
                            project_id=self.project_id,
                            project_name=self.project_name,
                        )
                        created.append(result)
                        break

        # Pattern 2: Repeated tool sequences (3+ same sequence)
        for i in range(len(self.observations) - 2):
            seq = [self.observations[i]["tool"], self.observations[i+1]["tool"]]
            for j in range(i + 2, len(self.observations) - 1):
                if [self.observations[j]["tool"], self.observations[j+1]["tool"]] == seq:
                    result = add_instinct(
                        trigger=f"when doing {seq[0]}",
                        action=f"follow with {seq[1]}",
                        domain="workflow",
                        confidence=0.5,
                        evidence={"sequence": seq, "occurrences": 2},
                        project_id=self.project_id,
                        project_name=self.project_name,
                    )
                    created.append(result)
                    break

        return created
