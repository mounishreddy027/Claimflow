import ast
from dataclasses import is_dataclass
from pathlib import Path

from claimflow.domain.claim import StateTransitionRecord
from claimflow.repositories.settlement_repository import PayoutRecord
from claimflow.repositories.subclaim_repository import SubClaim
from claimflow.services.assessment_engine import Assessment
from claimflow.types.audit import AuditLogEntry


def test_domain_layer_isolation_nfr_08() -> None:
    """NFR-08: Domain layer must have zero dependencies on repositories, services, or api."""
    domain_dir = Path(__file__).resolve().parent.parent.parent / "src" / "claimflow" / "domain"
    forbidden_prefixes = (
        "claimflow.api",
        "claimflow.services",
        "claimflow.repositories",
        "fastapi",
        "starlette",
        "sqlalchemy",
    )

    for py_file in domain_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(forbidden_prefixes), (
                        f"Domain file {py_file.name} illegal import: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(forbidden_prefixes), (
                    f"Domain file {py_file.name} illegal from-import: {node.module}"
                )


def test_repositories_layer_isolation() -> None:
    """Repositories must not import from the API/controller layer."""
    repo_dir = Path(__file__).resolve().parent.parent.parent / "src" / "claimflow" / "repositories"
    forbidden_prefixes = ("claimflow.api", "fastapi")

    for py_file in repo_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(forbidden_prefixes), (
                        f"Repo file {py_file.name} illegal import: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(forbidden_prefixes), (
                    f"Repo file {py_file.name} illegal from-import: {node.module}"
                )


def test_immutable_dataclasses_enforced() -> None:
    """NFR-02: Critical accounting and audit records must be frozen dataclasses."""
    immutable_classes = [
        AuditLogEntry,
        StateTransitionRecord,
        Assessment,
        PayoutRecord,
        SubClaim,
    ]
    for cls in immutable_classes:
        assert is_dataclass(cls), f"{cls.__name__} must be a dataclass"
        params = getattr(cls, "__dataclass_params__", None)  # type: ignore[attr-defined]
        assert params is not None and params.frozen is True, (
            f"{cls.__name__} must be frozen (immutable)"
        )
