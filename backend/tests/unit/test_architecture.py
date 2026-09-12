"""
Architecture tests.

These assert the dependency rules the layout is built on, so a violation fails
the build instead of being spotted in review (or not at all). Pure static
analysis of import lines — no database, no app startup.
"""

from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"

# ─── Tracked debt: none. Every rule below is live and unmarked. ───
# Three of these rules started out as xfail(strict=True) rather than being
# deleted or loosened, so each was stated and enforced from the moment it began
# to hold: a strict xfail that unexpectedly PASSES fails the build, which forces
# the marker off instead of letting it linger. All three came off that way:
#
#   - application layer vs. the ORM — rbac_service and user_service took an
#     AsyncSession and imported ORM models directly; both now depend only on
#     domain ports.
#   - session parameters in controllers — employee_import_controller imported
#     AsyncSession and ran raw select()/session.add() in a route body; it now
#     delegates to EmployeeImportService behind IEmployeeImportWriter.
#   - transaction boundaries — rbac_service called session.commit() seven times,
#     making each method its own transaction; porting it onto the repository
#     ports removed every one of those commits.
#
# If a new violation is introduced, fix the code. Do not re-add a marker here
# without the same commitment: strict, and naming the exact work that clears it.

# Encoding damage is what these guard against: a UTF-8 file read as Windows
# ANSI and re-saved becomes double-encoded, which round-trips back cleanly.
CP1252_REVERSE: dict[str, int] = {}
for _b in range(0x80, 0xA0):
    try:
        CP1252_REVERSE[bytes([_b]).decode("cp1252")] = _b
    except UnicodeDecodeError:
        CP1252_REVERSE[chr(_b)] = _b


def _import_lines(path: Path) -> list[tuple[int, str]]:
    """Every import statement in a file, as (line number, text)."""
    text = path.read_bytes().decode("utf-8-sig")
    return [
        (i, line.strip())
        for i, line in enumerate(text.splitlines(), 1)
        if line.strip().startswith(("import ", "from "))
    ]


def _python_files(*relative: str) -> list[Path]:
    return sorted(p for rel in relative for p in (SRC / rel).rglob("*.py"))


class TestLayerBoundaries:
    """
    Dependencies point inwards: domain <- application <- api/infrastructure.

    Controllers may wire concrete adapters, which is why the api layer is not
    covered by these rules.
    """

    def test_domain_does_not_import_outer_layers(self) -> None:
        offenders = [
            f"{path.relative_to(SRC)}:{lineno}  {line}"
            for path in _python_files("domain")
            for lineno, line in _import_lines(path)
            if "src.infrastructure" in line
            or "src.application" in line
            or "src.api" in line
            or "sqlalchemy" in line
            or "fastapi" in line
        ]
        assert not offenders, "domain must not depend on outer layers:\n" + "\n".join(
            offenders
        )

    def test_application_does_not_import_the_orm(self) -> None:
        """
        Services depend on domain ports, not on SQLAlchemy or ORM models.

        Note this checks for the ORM specifically, not all of `src.infrastructure`.
        Four services in this codebase (darwinbox, darwin_ad, esigner, ldap) still
        import their external HTTP client directly rather than through a domain
        port; that debt is tracked separately and is a different shape of problem
        from a service reaching for the database. Tightening this to the full
        `src.infrastructure` ban is the goal once those clients sit behind ports.
        """
        offenders = [
            f"{path.relative_to(SRC)}:{lineno}  {line}"
            for path in _python_files("application")
            for lineno, line in _import_lines(path)
            if "sqlalchemy" in line
            or "src.infrastructure.database" in line
            or "src.infrastructure.security" in line
        ]
        assert not offenders, (
            "application layer must not import the ORM or database/security "
            "infrastructure:\n" + "\n".join(offenders)
        )


class TestControllerBoundaries:
    """
    Controllers wire adapters together; they do not talk to the database themselves.

    A controller (or its private helper functions) taking `AsyncSession` as a parameter
    is the same violation whether it then runs a query directly or only uses the
    session to build a repository/adapter inline (`XRepositoryImpl(session)`,
    `PermissionManager(session)`, `AuditService(session)`) instead of receiving that
    adapter through a `Depends()` factory. Either way, the controller now knows about
    persistence machinery it should not — see `.kiro/steering/api-layer-standard.md`.
    """

    def test_no_session_parameter_in_endpoints(self) -> None:
        offenders = [
            f"{path.relative_to(SRC)}:{lineno}  {line}"
            for path in _python_files("api/v1/endpoints")
            for lineno, line in _import_lines(path)
            if "sqlalchemy" in line
        ]
        assert not offenders, (
            "controllers must not import sqlalchemy or AsyncSession — depend on a "
            "repository/port from dependencies.py instead:\n" + "\n".join(offenders)
        )


class TestTransactionBoundaries:
    """
    Only the session module and the UnitOfWork may commit.

    Everything else either runs inside a request (where `get_db_session` commits
    once at the end) or goes through `UnitOfWork.commit()`. Repositories flush;
    they never commit.
    """

    ALLOWED = {"session.py", "unit_of_work.py"}

    def test_only_session_and_unit_of_work_commit(self) -> None:
        offenders: list[str] = []
        for path in sorted(SRC.rglob("*.py")):
            if path.name in self.ALLOWED:
                continue
            text = path.read_bytes().decode("utf-8-sig")
            for lineno, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "session.commit()" in stripped or "_session.commit()" in stripped:
                    offenders.append(f"{path.relative_to(SRC)}:{lineno}  {stripped}")
        assert not offenders, (
            "only session.py and unit_of_work.py may commit; use UnitOfWork.commit() "
            "or let get_db_session commit at the end of the request:\n"
            + "\n".join(offenders)
        )


class TestSourceEncoding:
    """Guards against the double-encoding that mangled a file in this codebase."""

    @staticmethod
    def _to_ansi(text: str) -> bytes:
        out = bytearray()
        for ch in text:
            if ch in CP1252_REVERSE:
                out.append(CP1252_REVERSE[ch])
            elif ord(ch) < 0x100:
                out.append(ord(ch))
            else:
                raise UnicodeEncodeError("cp1252", ch, 0, 1, "not representable")
        return bytes(out)

    def test_no_double_encoded_lines(self) -> None:
        offenders: list[str] = []
        for path in sorted(SRC.rglob("*.py")):
            text = path.read_bytes().decode("utf-8-sig")
            for lineno, line in enumerate(text.splitlines(), 1):
                if line.isascii():
                    continue
                try:
                    if self._to_ansi(line).decode("utf-8") != line:
                        offenders.append(f"{path.relative_to(SRC)}:{lineno}")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    continue  # genuinely-encoded text cannot be reversed
        assert not offenders, (
            "these lines look double-encoded (UTF-8 read as cp1252, re-saved):\n"
            + "\n".join(offenders)
        )

    def test_sources_have_no_byte_order_mark(self) -> None:
        """
        Python assumes UTF-8, so a BOM adds nothing and causes real trouble: it
        broke a codemod during this work, and mixed encodings are what let a file
        become double-encoded in the first place. Keep the tree uniform.
        """
        offenders = [
            str(path.relative_to(SRC))
            for path in sorted(SRC.rglob("*.py"))
            if path.read_bytes().startswith(b"\xef\xbb\xbf")
        ]
        assert not offenders, (
            f"{len(offenders)} file(s) start with a UTF-8 BOM; save as UTF-8 "
            "without one:\n" + "\n".join(offenders)
        )
