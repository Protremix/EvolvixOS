"""
Audit & Compliance Reporting — Phase 44

Comprehensive audit trails, compliance framework tracking (GDPR, SOC2, ISO27001, AML/KYC),
automated compliance checks, risk assessment, policy management, and reporting.
"""

import secrets
import time
import threading
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from app.core.logging import get_logger

logger = get_logger("service.audit_compliance")


class AuditCategory(str, Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION = "configuration"
    TRANSACTION = "transaction"
    SECURITY = "security"
    GOVERNANCE = "governance"
    DEPLOYMENT = "deployment"
    SYSTEM = "system"


class AuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ComplianceFramework(str, Enum):
    GDPR = "gdpr"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    AML_KYC = "aml_kyc"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    CCPA = "ccpa"
    CUSTOM = "custom"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    PENDING_REVIEW = "pending_review"
    NOT_APPLICABLE = "not_applicable"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    id: str
    category: str
    action: str
    actor: str  # user/system/api_key
    resource: str  # affected resource path/ID
    details: str = ""
    severity: str = AuditSeverity.INFO.value
    ip_address: str = ""
    user_agent: str = ""
    result: str = "success"  # success/failure
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    correlation_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ComplianceCheck:
    id: str
    framework: str
    control_id: str  # e.g. "GDPR-6.1", "SOC2-CC1.1"
    title: str
    description: str
    status: str = ComplianceStatus.PENDING_REVIEW.value
    evidence: list = field(default_factory=list)
    last_checked: str = ""
    last_passed: str = ""
    last_failed: str = ""
    check_count: int = 0
    pass_count: int = 0
    fail_count: int = 0
    risk_level: str = RiskLevel.MEDIUM.value
    remediation: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ComplianceReport:
    id: str
    framework: str
    title: str
    period_start: str
    period_end: str
    total_controls: int = 0
    compliant: int = 0
    non_compliant: int = 0
    partially_compliant: int = 0
    pending: int = 0
    compliance_score: float = 0.0
    generated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    summary: str = ""
    findings: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Policy:
    id: str
    name: str
    description: str
    framework: str
    rule_type: str  # access_control, data_retention, encryption, etc.
    enabled: bool = True
    enforced: bool = True
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated: str = ""
    violations: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RiskAssessment:
    id: str
    title: str
    description: str
    risk_level: str = RiskLevel.MEDIUM.value
    probability: float = 0.5  # 0-1
    impact: float = 0.5  # 0-1
    risk_score: float = 0.25  # probability * impact
    mitigation: str = ""
    status: str = "open"  # open, mitigated, accepted, closed
    owner: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class AuditComplianceService:
    """Audit trails and compliance reporting."""

    def __init__(self, max_audit: int = 50000, max_reports: int = 1000):
        self._audit_entries: deque = deque(maxlen=max_audit)
        self._audit_by_id: dict[str, AuditEntry] = {}
        self._compliance_checks: dict[str, ComplianceCheck] = {}
        self._reports: dict[str, ComplianceReport] = {}
        self._policies: dict[str, Policy] = {}
        self._risks: dict[str, RiskAssessment] = {}
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._init_default_checks()
        self._init_default_policies()
        self._init_sample_audits()

    def _init_default_checks(self):
        """Initialize default compliance checks for each framework."""
        checks = [
            # GDPR
            ("gdpr", "GDPR-6.1", "Lawfulness of Processing", "Ensure all data processing has legal basis", RiskLevel.HIGH.value),
            ("gdpr", "GDPR-7.1", "Data Subject Rights", "Mechanisms for data access, rectification, erasure", RiskLevel.HIGH.value),
            ("gdpr", "GDPR-8.1", "Data Breach Notification", "72-hour breach notification process", RiskLevel.CRITICAL.value),
            ("gdpr", "GDPR-9.1", "Privacy by Design", "Data protection built into systems by default", RiskLevel.MEDIUM.value),
            ("gdpr", "GDPR-10.1", "Records of Processing", "Maintain processing activity records", RiskLevel.MEDIUM.value),
            # SOC2
            ("soc2", "SOC2-CC1.1", "Control Environment", "Integrity and ethical values established", RiskLevel.HIGH.value),
            ("soc2", "SOC2-CC2.1", "Communication", "Internal and external communication of controls", RiskLevel.MEDIUM.value),
            ("soc2", "SOC2-CC3.1", "Risk Assessment", "Identify and assess risks to objectives", RiskLevel.HIGH.value),
            ("soc2", "SOC2-CC4.1", "Monitoring Activities", "Ongoing evaluations of controls", RiskLevel.MEDIUM.value),
            ("soc2", "SOC2-CC6.1", "Logical Access", "Access controls and authentication", RiskLevel.CRITICAL.value),
            ("soc2", "SOC2-CC6.6", "Encryption", "Data encryption at rest and in transit", RiskLevel.CRITICAL.value),
            ("soc2", "SOC2-CC7.1", "System Monitoring", "Monitor system performance and security", RiskLevel.HIGH.value),
            # ISO27001
            ("iso27001", "ISO-A.5", "Information Security Policies", "Documented security policies", RiskLevel.HIGH.value),
            ("iso27001", "ISO-A.8", "Asset Management", "Inventory and classification of assets", RiskLevel.MEDIUM.value),
            ("iso27001", "ISO-A.9", "Access Control", "Access control policy and management", RiskLevel.HIGH.value),
            ("iso27001", "ISO-A.10", "Cryptography", "Encryption policy and key management", RiskLevel.CRITICAL.value),
            ("iso27001", "ISO-A.12", "Operations Security", "Operational procedures and controls", RiskLevel.HIGH.value),
            ("iso27001", "ISO-A.16", "Incident Management", "Incident response and management", RiskLevel.CRITICAL.value),
            # AML/KYC
            ("aml_kyc", "AML-1.1", "Customer Due Diligence", "Identity verification for all customers", RiskLevel.CRITICAL.value),
            ("aml_kyc", "AML-2.1", "Transaction Monitoring", "Monitor for suspicious transactions", RiskLevel.HIGH.value),
            ("aml_kyc", "AML-3.1", "Sanctions Screening", "Screen against sanctions lists", RiskLevel.CRITICAL.value),
            ("aml_kyc", "AML-4.1", "Suspicious Activity Reports", "File SARs for suspicious activity", RiskLevel.HIGH.value),
            ("aml_kyc", "AML-5.1", "Record Keeping", "Maintain transaction records for 5 years", RiskLevel.MEDIUM.value),
        ]

        for framework, control_id, title, desc, risk in checks:
            check_id = f"chk-{secrets.token_hex(8)}"
            check = ComplianceCheck(
                id=check_id, framework=framework, control_id=control_id,
                title=title, description=desc, risk_level=risk,
                status=ComplianceStatus.COMPLIANT.value,
                last_checked=datetime.utcnow().isoformat(),
                last_passed=datetime.utcnow().isoformat(),
            )
            # Simulate some checks being partially compliant or pending
            import random
            random.seed(42)
            check.status = random.choices(
                [ComplianceStatus.COMPLIANT.value, ComplianceStatus.PARTIALLY_COMPLIANT.value,
                 ComplianceStatus.PENDING_REVIEW.value, ComplianceStatus.NON_COMPLIANT.value],
                weights=[60, 20, 15, 5]
            )[0]
            check.check_count = random.randint(5, 50)
            check.pass_count = random.randint(3, 48)
            check.fail_count = check.check_count - check.pass_count
            self._compliance_checks[check_id] = check

    def _init_default_policies(self):
        """Initialize default compliance policies."""
        policies = [
            ("Data Retention Policy", "Retain user data for maximum 7 years, then purge", "gdpr", "data_retention"),
            ("Access Control Policy", "Role-based access with principle of least privilege", "soc2", "access_control"),
            ("Encryption Policy", "AES-256 at rest, TLS 1.3 in transit", "iso27001", "encryption"),
            ("KYC Verification Policy", "All users must complete KYC before transactions", "aml_kyc", "verification"),
            ("Incident Response Policy", "Security incidents must be reported within 1 hour", "iso27001", "incident_response"),
            ("Audit Logging Policy", "All system actions must be logged with timestamps", "soc2", "audit_logging"),
            ("Data Minimization Policy", "Collect only necessary data", "gdpr", "data_minimization"),
            ("Password Policy", "Minimum 12 chars, special chars, 90-day rotation", "soc2", "password"),
        ]
        for name, desc, framework, rule_type in policies:
            pid = f"pol-{secrets.token_hex(8)}"
            self._policies[pid] = Policy(
                id=pid, name=name, description=desc,
                framework=framework, rule_type=rule_type,
            )

    def _init_sample_audits(self):
        """Initialize with sample audit entries."""
        import random
        random.seed(42)
        categories = [c.value for c in AuditCategory]
        severities = [s.value for s in AuditSeverity]
        actions = ["login", "logout", "create", "update", "delete", "transfer", "stake", "vote", "deploy", "config_change"]
        actors = ["0xverdis", "0xadmin", "0xuser1", "0xuser2", "system", "api_key_1"]

        for i in range(500):
            entry = AuditEntry(
                id=f"aud-{secrets.token_hex(8)}",
                category=random.choice(categories),
                action=random.choice(actions),
                actor=random.choice(actors),
                resource=f"/api/v1/{random.choice(['staking', 'governance', 'identity', 'bridge', 'tokens'])}/{secrets.token_hex(4)}",
                severity=random.choices(severities, weights=[60, 25, 10, 5])[0],
                result=random.choices(["success", "failure"], weights=[90, 10])[0],
                ip_address=f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
                timestamp=(datetime.utcnow() - timedelta(hours=random.randint(0, 720))).isoformat(),
                correlation_id=f"corr-{secrets.token_hex(8)}" if random.random() > 0.5 else "",
            )
            self._audit_entries.append(entry)
            self._audit_by_id[entry.id] = entry

    # === Audit Trail ===

    def record_audit(self, category: str, action: str, actor: str, resource: str,
                     details: str = "", severity: str = AuditSeverity.INFO.value,
                     ip_address: str = "", user_agent: str = "",
                     result: str = "success", metadata: dict = None,
                     correlation_id: str = "") -> AuditEntry:
        """Record an audit entry."""
        entry_id = f"aud-{secrets.token_hex(8)}"
        entry = AuditEntry(
            id=entry_id, category=category, action=action, actor=actor,
            resource=resource, details=details, severity=severity,
            ip_address=ip_address, user_agent=user_agent, result=result,
            metadata=metadata or {}, correlation_id=correlation_id,
        )
        with self._lock:
            self._audit_entries.append(entry)
            self._audit_by_id[entry_id] = entry
        logger.info("audit_recorded", id=entry_id, category=category, action=action, actor=actor)
        return entry

    def get_audit(self, audit_id: str) -> Optional[AuditEntry]:
        return self._audit_by_id.get(audit_id)

    def list_audit(
        self, category: str = None, actor: str = None, severity: str = None,
        result: str = None, start_date: str = None, end_date: str = None,
        limit: int = 50, sort_by: str = "timestamp",
    ) -> list[AuditEntry]:
        entries = list(self._audit_entries)
        if category:
            entries = [e for e in entries if e.category == category]
        if actor:
            entries = [e for e in entries if e.actor == actor]
        if severity:
            entries = [e for e in entries if e.severity == severity]
        if result:
            entries = [e for e in entries if e.result == result]
        if start_date:
            entries = [e for e in entries if e.timestamp >= start_date]
        if end_date:
            entries = [e for e in entries if e.timestamp <= end_date]

        entries.sort(key=lambda e: getattr(e, sort_by, e.timestamp), reverse=True)
        return entries[:limit]

    def get_audit_stats(self, hours: int = 24) -> dict:
        """Get audit statistics."""
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        recent = [e for e in self._audit_entries if e.timestamp >= cutoff]

        by_category = defaultdict(int)
        by_severity = defaultdict(int)
        by_actor = defaultdict(int)
        by_result = defaultdict(int)

        for e in recent:
            by_category[e.category] += 1
            by_severity[e.severity] += 1
            by_actor[e.actor] += 1
            by_result[e.result] += 1

        return {
            "total_entries": len(recent),
            "by_category": dict(by_category),
            "by_severity": dict(by_severity),
            "by_actor": dict(by_actor),
            "by_result": dict(by_result),
            "failures": by_result.get("failure", 0),
            "critical_events": by_severity.get("critical", 0),
            "period_hours": hours,
        }

    # === Compliance Checks ===

    def list_compliance_checks(self, framework: str = None, status: str = None) -> list[ComplianceCheck]:
        checks = list(self._compliance_checks.values())
        if framework:
            checks = [c for c in checks if c.framework == framework]
        if status:
            checks = [c for c in checks if c.status == status]
        return checks

    def get_compliance_check(self, check_id: str) -> Optional[ComplianceCheck]:
        return self._compliance_checks.get(check_id)

    def update_compliance_check(self, check_id: str, **kwargs) -> Optional[ComplianceCheck]:
        check = self._compliance_checks.get(check_id)
        if not check:
            return None
        for k, v in kwargs.items():
            if hasattr(check, k):
                setattr(check, k, v)
        check.last_checked = datetime.utcnow().isoformat()
        return check

    def run_compliance_check(self, check_id: str) -> Optional[ComplianceCheck]:
        """Run a compliance check (simulated)."""
        check = self._compliance_checks.get(check_id)
        if not check:
            return None
        check.check_count += 1
        # Simulate: mostly pass
        import random
        if random.random() > 0.1:
            check.status = ComplianceStatus.COMPLIANT.value
            check.pass_count += 1
            check.last_passed = datetime.utcnow().isoformat()
        else:
            check.status = ComplianceStatus.NON_COMPLIANT.value
            check.fail_count += 1
            check.last_failed = datetime.utcnow().isoformat()
        check.last_checked = datetime.utcnow().isoformat()
        return check

    def run_all_checks(self, framework: str = None) -> dict:
        """Run all compliance checks for a framework."""
        checks = self.list_compliance_checks(framework)
        passed = 0
        failed = 0
        for c in checks:
            result = self.run_compliance_check(c.id)
            if result and result.status == ComplianceStatus.COMPLIANT.value:
                passed += 1
            else:
                failed += 1
        return {
            "total": len(checks),
            "passed": passed,
            "failed": failed,
            "framework": framework or "all",
        }

    # === Compliance Reports ===

    def generate_report(self, framework: str, title: str, period_days: int = 30) -> ComplianceReport:
        """Generate a compliance report for a framework."""
        checks = self.list_compliance_checks(framework)
        compliant = sum(1 for c in checks if c.status == ComplianceStatus.COMPLIANT.value)
        non_compliant = sum(1 for c in checks if c.status == ComplianceStatus.NON_COMPLIANT.value)
        partial = sum(1 for c in checks if c.status == ComplianceStatus.PARTIALLY_COMPLIANT.value)
        pending = sum(1 for c in checks if c.status == ComplianceStatus.PENDING_REVIEW.value)
        total = len(checks)
        score = round(compliant / max(1, total) * 100, 2)

        findings = []
        recommendations = []
        for c in checks:
            if c.status == ComplianceStatus.NON_COMPLIANT.value:
                findings.append(f"{c.control_id}: {c.title} — NON-COMPLIANT")
                recommendations.append(f"Remediate {c.control_id}: {c.remediation or c.description}")
            elif c.status == ComplianceStatus.PARTIALLY_COMPLIANT.value:
                findings.append(f"{c.control_id}: {c.title} — PARTIALLY COMPLIANT")
                recommendations.append(f"Complete implementation of {c.control_id}")

        report_id = f"rpt-{secrets.token_hex(8)}"
        report = ComplianceReport(
            id=report_id, framework=framework, title=title,
            period_start=(datetime.utcnow() - timedelta(days=period_days)).isoformat(),
            period_end=datetime.utcnow().isoformat(),
            total_controls=total, compliant=compliant,
            non_compliant=non_compliant, partially_compliant=partial,
            pending=pending, compliance_score=score,
            findings=findings, recommendations=recommendations,
            summary=f"{framework.upper()} compliance at {score}% — {compliant}/{total} controls fully compliant",
        )
        self._reports[report_id] = report
        return report

    def list_reports(self, framework: str = None, limit: int = 50) -> list[ComplianceReport]:
        reports = list(self._reports.values())
        if framework:
            reports = [r for r in reports if r.framework == framework]
        reports.sort(key=lambda r: r.generated, reverse=True)
        return reports[:limit]

    def get_report(self, report_id: str) -> Optional[ComplianceReport]:
        return self._reports.get(report_id)

    # === Policies ===

    def list_policies(self, framework: str = None) -> list[Policy]:
        policies = list(self._policies.values())
        if framework:
            policies = [p for p in policies if p.framework == framework]
        return policies

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        return self._policies.get(policy_id)

    def create_policy(self, name: str, description: str, framework: str,
                      rule_type: str, metadata: dict = None) -> Policy:
        pid = f"pol-{secrets.token_hex(8)}"
        policy = Policy(
            id=pid, name=name, description=description,
            framework=framework, rule_type=rule_type,
            metadata=metadata or {},
        )
        self._policies[pid] = policy
        return policy

    def update_policy(self, policy_id: str, **kwargs) -> Optional[Policy]:
        policy = self._policies.get(policy_id)
        if not policy:
            return None
        for k, v in kwargs.items():
            if hasattr(policy, k):
                setattr(policy, k, v)
        policy.updated = datetime.utcnow().isoformat()
        return policy

    def delete_policy(self, policy_id: str) -> bool:
        return self._policies.pop(policy_id, None) is not None

    def record_policy_violation(self, policy_id: str) -> Optional[Policy]:
        policy = self._policies.get(policy_id)
        if policy:
            policy.violations += 1
        return policy

    # === Risk Assessment ===

    def create_risk(self, title: str, description: str, probability: float = 0.5,
                    impact: float = 0.5, mitigation: str = "", owner: str = "") -> RiskAssessment:
        risk_id = f"rsk-{secrets.token_hex(8)}"
        risk_level = RiskLevel.LOW.value
        score = probability * impact
        if score >= 0.7:
            risk_level = RiskLevel.CRITICAL.value
        elif score >= 0.4:
            risk_level = RiskLevel.HIGH.value
        elif score >= 0.2:
            risk_level = RiskLevel.MEDIUM.value

        risk = RiskAssessment(
            id=risk_id, title=title, description=description,
            risk_level=risk_level, probability=probability,
            impact=impact, risk_score=round(score, 2),
            mitigation=mitigation, owner=owner,
        )
        self._risks[risk_id] = risk
        return risk

    def list_risks(self, status: str = None, risk_level: str = None) -> list[RiskAssessment]:
        risks = list(self._risks.values())
        if status:
            risks = [r for r in risks if r.status == status]
        if risk_level:
            risks = [r for r in risks if r.risk_level == risk_level]
        risks.sort(key=lambda r: r.risk_score, reverse=True)
        return risks

    def get_risk(self, risk_id: str) -> Optional[RiskAssessment]:
        return self._risks.get(risk_id)

    def update_risk(self, risk_id: str, **kwargs) -> Optional[RiskAssessment]:
        risk = self._risks.get(risk_id)
        if not risk:
            return None
        for k, v in kwargs.items():
            if hasattr(risk, k):
                setattr(risk, k, v)
        risk.updated = datetime.utcnow().isoformat()
        # Recalculate risk level
        risk.risk_score = round(risk.probability * risk.impact, 2)
        if risk.risk_score >= 0.7:
            risk.risk_level = RiskLevel.CRITICAL.value
        elif risk.risk_score >= 0.4:
            risk.risk_level = RiskLevel.HIGH.value
        elif risk.risk_score >= 0.2:
            risk.risk_level = RiskLevel.MEDIUM.value
        else:
            risk.risk_level = RiskLevel.LOW.value
        return risk

    def delete_risk(self, risk_id: str) -> bool:
        return self._risks.pop(risk_id, None) is not None

    # === Dashboard ===

    def get_dashboard(self) -> dict:
        frameworks = set(c.framework for c in self._compliance_checks.values())
        framework_summary = {}
        for fw in frameworks:
            checks = [c for c in self._compliance_checks.values() if c.framework == fw]
            compliant = sum(1 for c in checks if c.status == ComplianceStatus.COMPLIANT.value)
            framework_summary[fw] = {
                "total": len(checks),
                "compliant": compliant,
                "score": round(compliant / max(1, len(checks)) * 100, 2),
            }

        risks = list(self._risks.values())
        open_risks = [r for r in risks if r.status == "open"]

        return {
            "audit_stats_24h": self.get_audit_stats(24),
            "total_audit_entries": len(self._audit_entries),
            "frameworks": framework_summary,
            "total_checks": len(self._compliance_checks),
            "total_policies": len(self._policies),
            "total_risks": len(risks),
            "open_risks": len(open_risks),
            "critical_risks": sum(1 for r in risks if r.risk_level == RiskLevel.CRITICAL.value),
            "total_reports": len(self._reports),
            "monitoring": self._monitoring,
        }

    # === Monitoring ===

    def start_monitoring(self, interval: int = 300):
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._monitor_thread.start()
        logger.info("audit_monitoring_started", interval=interval)

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval: int):
        while self._monitoring:
            try:
                # Run random compliance checks
                import random
                checks = list(self._compliance_checks.values())
                if checks:
                    sample = random.sample(checks, min(3, len(checks)))
                    for c in sample:
                        self.run_compliance_check(c.id)
            except Exception as e:
                logger.error("monitor_error", error=str(e))
            time.sleep(interval)

    def is_monitoring(self) -> bool:
        return self._monitoring

    # === Frameworks ===

    def list_frameworks(self) -> list[dict]:
        return [{"value": f.value, "name": f.value.upper(), "display": f.value.replace("_", "/").upper()} for f in ComplianceFramework]


_service: Optional[AuditComplianceService] = None

def get_audit_compliance_service() -> AuditComplianceService:
    global _service
    if _service is None:
        _service = AuditComplianceService()
    return _service
