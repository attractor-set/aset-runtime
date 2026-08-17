from __future__ import annotations

import argparse
import ast
import builtins
import io
import itertools
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from tools.alpha4_runtime_seed_extension import parse_seed_binding, sha256, tree_digest

ROOT = Path(__file__).resolve().parents[1]


_ALLOWED_DIRECT_IMPORTS = frozenset({"hashlib"})
_ALLOWED_FROM_IMPORTS = {
    "copy": frozenset({"deepcopy"}),
    "pathlib": frozenset({"Path"}),
}
_FILESYSTEM_INSPECTION_METHODS = frozenset(
    {
        "absolute",
        "cwd",
        "exists",
        "expanduser",
        "glob",
        "group",
        "home",
        "is_block_device",
        "is_char_device",
        "is_dir",
        "is_fifo",
        "is_file",
        "is_mount",
        "is_socket",
        "is_symlink",
        "iterdir",
        "lstat",
        "owner",
        "readlink",
        "resolve",
        "rglob",
        "samefile",
        "stat",
        "walk",
    }
)


class AirgapError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AirgapError(message)


def _validate_companion_ast(
    source: str, *, allowed_imports: frozenset[str], allow_seed_loader: bool
) -> None:
    tree = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    def enclosing_function(node: ast.AST) -> str | None:
        current = node
        while current in parents:
            current = parents[current]
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return current.name
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                require(
                    alias.asname is None
                    and alias.name in allowed_imports
                    and alias.name in _ALLOWED_DIRECT_IMPORTS,
                    f"air-gap companion import forbidden: {alias.name}",
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imported = {alias.name for alias in node.names}
            require(node.level == 0, "air-gap companion relative import forbidden")
            if module == "__future__":
                require(
                    imported == {"annotations"}
                    and all(alias.asname is None for alias in node.names),
                    "air-gap companion future import drift",
                )
            else:
                require(
                    module in allowed_imports
                    and module in _ALLOWED_FROM_IMPORTS
                    and imported <= _ALLOWED_FROM_IMPORTS[module]
                    and all(alias.asname is None for alias in node.names),
                    f"air-gap companion import forbidden: {module}",
                )
        elif isinstance(node, ast.Name) and node.id == "__builtins__":
            raise AirgapError("air-gap companion accesses __builtins__")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise AirgapError(f"air-gap companion private attribute forbidden: {node.attr}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {
                "__import__",
                "breakpoint",
                "delattr",
                "dir",
                "eval",
                "getattr",
                "globals",
                "help",
                "input",
                "locals",
                "setattr",
                "type",
                "vars",
            }:
                raise AirgapError(f"air-gap companion dynamic capability forbidden: {node.func.id}")
            if node.func.id in {"exec", "compile"}:
                require(
                    allow_seed_loader and enclosing_function(node) == "_load_seed_base",
                    f"air-gap companion {node.func.id} permitted only for exact Seed base loader",
                )
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            require(
                node.func.attr not in _FILESYSTEM_INSPECTION_METHODS,
                f"air-gap companion filesystem inspection forbidden: {node.func.attr}",
            )
            require(
                node.func.attr
                not in {
                    "write_text",
                    "write_bytes",
                    "unlink",
                    "rename",
                    "replace",
                    "mkdir",
                    "touch",
                    "chmod",
                    "symlink_to",
                    "hardlink_to",
                },
                f"air-gap companion filesystem mutation forbidden: {node.func.attr}",
            )
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            lowered = node.value.lower()
            require(
                not any(
                    marker in lowered for marker in ("tools.", "tools/", ".tla", ".forth", ".petri")
                ),
                "air-gap companion embeds repository semantic-source locator",
            )


def _load_expression(
    path: Path,
    allowed_root: Path,
    *,
    allowed_imports: frozenset[str],
    allow_seed_loader: bool,
) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    _validate_companion_ast(
        source, allowed_imports=allowed_imports, allow_seed_loader=allow_seed_loader
    )
    allowed_root = allowed_root.resolve()
    original_io_open = io.open

    def guarded_open(file: object, *args: object, **kwargs: object):
        if isinstance(file, int):
            return original_io_open(file, *args, **kwargs)
        mode = kwargs.get("mode", args[0] if args else "r")
        require(
            isinstance(mode, str) and not any(flag in mode for flag in "wax+"),
            "air-gap companion file access must be read-only",
        )
        candidate = Path(file).resolve()  # type: ignore[arg-type]
        require(
            candidate == allowed_root or allowed_root in candidate.parents,
            f"air-gap companion file access escaped materialized profile tree: {candidate}",
        )
        return original_io_open(file, *args, **kwargs)

    original_import = builtins.__import__

    def guarded_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        requested = set(fromlist or ())
        if level != 0:
            raise ImportError("air-gap companion relative import forbidden")
        if name == "__future__":
            if requested != {"annotations"}:
                raise ImportError("air-gap companion future import drift")
        elif name in _ALLOWED_DIRECT_IMPORTS:
            if name not in allowed_imports or requested:
                raise ImportError(f"air-gap companion import forbidden: {name}")
        elif name in _ALLOWED_FROM_IMPORTS:
            if (
                name not in allowed_imports
                or not requested
                or not requested <= _ALLOWED_FROM_IMPORTS[name]
            ):
                raise ImportError(f"air-gap companion import forbidden: {name}")
        else:
            raise ImportError(f"air-gap companion import forbidden: {name}")
        return original_import(name, globals, locals, fromlist, level)

    safe_builtins = dict(vars(builtins))
    safe_builtins["__import__"] = guarded_import
    safe_builtins["open"] = guarded_open

    def guarded_exec(
        code: object,
        globals_dict: dict[str, Any] | None = None,
        locals_dict: dict[str, Any] | None = None,
    ) -> None:
        target_globals = {} if globals_dict is None else globals_dict
        target_globals.setdefault("__builtins__", safe_builtins)
        exec(code, target_globals, locals_dict)

    safe_builtins["exec"] = guarded_exec
    namespace: dict[str, Any] = {
        "__file__": str(path),
        "__name__": "aset_runtime_alpha4_airgap_subject",
        "__builtins__": safe_builtins,
    }
    io.open = guarded_open  # type: ignore[assignment]
    try:
        exec(compile(source, str(path), "exec"), namespace)
    finally:
        io.open = original_io_open  # type: ignore[assignment]
    return namespace


def _starts() -> list[dict[str, Any]]:
    return [
        {
            "attempt_id": attempt_id,
            "attempt_digest": attempt_digest,
            "runtime_binding": "runtime:0",
            "descriptor_binding": "descriptor:0",
        }
        for attempt_id in ("a0", "a1")
        for attempt_digest in ("d0", "d1")
    ]


def _terminals() -> list[dict[str, Any]]:
    return [
        {
            "attempt_id": attempt_id,
            "attempt_digest": attempt_digest,
            "terminal_kind": terminal_kind,
            "terminal_digest": terminal_digest,
            "terminal_binding": "terminal-binding:0",
            "evidence_bindings": ["e0"],
        }
        for attempt_id in ("a0", "a1")
        for attempt_digest in ("d0", "d1")
        for terminal_kind in ("RESULT", "NO_RESULT")
        for terminal_digest in ("t0", "t1")
    ]


def _states() -> list[dict[str, list[dict[str, Any]]]]:
    starts = _starts()
    terminals = _terminals()
    starts_by_id = {
        attempt_id: [item for item in starts if item["attempt_id"] == attempt_id]
        for attempt_id in ("a0", "a1")
    }
    states: list[dict[str, list[dict[str, Any]]]] = []
    start_choices = [[None, *starts_by_id[attempt_id]] for attempt_id in ("a0", "a1")]
    for selected in itertools.product(*start_choices):
        selected_starts = [deepcopy(item) for item in selected if item is not None]
        if not selected_starts:
            states.append({"starts": [], "terminals": []})
            continue
        terminal_choices: list[list[dict[str, Any] | None]] = []
        for start in selected_starts:
            matching = [
                item
                for item in terminals
                if item["attempt_id"] == start["attempt_id"]
                and item["attempt_digest"] == start["attempt_digest"]
            ]
            terminal_choices.append([None, *matching])
        for chosen_terminals in itertools.product(*terminal_choices):
            states.append(
                {
                    "starts": deepcopy(selected_starts),
                    "terminals": [deepcopy(item) for item in chosen_terminals if item is not None],
                }
            )
    return states


def _result(accepted: bool, code: str, changed: bool) -> dict[str, Any]:
    return {
        "accepted": accepted,
        "code": code,
        "state_changed": changed,
        "seed_projection": {"action": "STUTTER", "effect_permitted": False},
    }


def _terminal_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    scalar_fields = {
        "attempt_id",
        "attempt_digest",
        "terminal_kind",
        "terminal_digest",
        "terminal_binding",
    }
    return all(left[field] == right[field] for field in scalar_fields) and set(
        left["evidence_bindings"]
    ) == set(right["evidence_bindings"])


def _expected_start(
    state: dict[str, list[dict[str, Any]]], start: dict[str, Any]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    next_state = deepcopy(state)
    same_id = [item for item in next_state["starts"] if item["attempt_id"] == start["attempt_id"]]
    if start in same_id:
        return next_state, _result(True, "IDEMPOTENT_REPLAY", False)
    if same_id:
        return next_state, _result(False, "ATTEMPT_IDENTITY_CONFLICT", False)
    next_state["starts"].append(deepcopy(start))
    return next_state, _result(True, "ATTEMPT_STARTED", True)


def _expected_end(
    state: dict[str, list[dict[str, Any]]], terminal: dict[str, Any]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    next_state = deepcopy(state)
    same_id = [
        item for item in next_state["terminals"] if item["attempt_id"] == terminal["attempt_id"]
    ]
    if any(_terminal_equal(item, terminal) for item in same_id):
        return next_state, _result(True, "IDEMPOTENT_REPLAY", False)
    if same_id:
        return next_state, _result(False, "TERMINAL_ATTEMPT_IMMUTABLE", False)
    matching = any(
        item["attempt_id"] == terminal["attempt_id"]
        and item["attempt_digest"] == terminal["attempt_digest"]
        for item in next_state["starts"]
    )
    if not matching:
        return next_state, _result(False, "ATTEMPT_NOT_RUNNING", False)
    next_state["terminals"].append(deepcopy(terminal))
    code = (
        "ATTEMPT_ENDED_WITH_RESULT"
        if terminal["terminal_kind"] == "RESULT"
        else "ATTEMPT_ENDED_WITH_NO_RESULT"
    )
    return next_state, _result(True, code, True)


def _check_identity_sensitivity(namespace: dict[str, Any], seed_state: dict[str, Any]) -> int:
    identity_checks = 0
    identity_start = {
        "attempt_id": "identity-a",
        "attempt_digest": "identity-d",
        "runtime_binding": "runtime:0",
        "descriptor_binding": "descriptor:0",
    }
    identity_state = {"starts": [deepcopy(identity_start)], "terminals": []}
    for field, replacement_value in (
        ("runtime_binding", "runtime:1"),
        ("descriptor_binding", "descriptor:1"),
    ):
        candidate = {**identity_start, field: replacement_value}
        expected_state, expected_result = _expected_start(identity_state, candidate)
        actual_state, actual_seed, actual_result = namespace["start_attempt"](
            deepcopy(identity_state), deepcopy(candidate), deepcopy(seed_state)
        )
        require(
            actual_state == expected_state,
            f"Runtime start identity sensitivity state mismatch: {field}",
        )
        require(
            actual_result == expected_result,
            f"Runtime start identity sensitivity result mismatch: {field}",
        )
        require(actual_seed == seed_state, "Runtime start identity sensitivity changed Seed state")
        identity_checks += 1

    set_start = {
        "attempt_id": "set-a",
        "attempt_digest": "set-d",
        "runtime_binding": "runtime:set",
        "descriptor_binding": "descriptor:set",
    }
    set_terminal = {
        "attempt_id": "set-a",
        "attempt_digest": "set-d",
        "terminal_kind": "RESULT",
        "terminal_digest": "set-t",
        "terminal_binding": "terminal-binding:set",
        "evidence_bindings": ["e0", "e1"],
    }
    terminal_state = {"starts": [deepcopy(set_start)], "terminals": [deepcopy(set_terminal)]}
    for field, replacement_value in (
        ("terminal_binding", "terminal-binding:other"),
        ("evidence_bindings", ["e0", "e2"]),
    ):
        candidate = {**set_terminal, field: replacement_value}
        expected_state, expected_result = _expected_end(terminal_state, candidate)
        actual_state, actual_seed, actual_result = namespace["end_attempt"](
            deepcopy(terminal_state), deepcopy(candidate), deepcopy(seed_state)
        )
        require(
            actual_state == expected_state,
            f"Runtime terminal identity sensitivity state mismatch: {field}",
        )
        require(
            actual_result == expected_result,
            f"Runtime terminal identity sensitivity result mismatch: {field}",
        )
        require(
            actual_seed == seed_state,
            "Runtime terminal identity sensitivity changed Seed state",
        )
        identity_checks += 1

    reordered = {**set_terminal, "evidence_bindings": ["e1", "e0"]}
    expected_state, expected_result = _expected_end(terminal_state, reordered)
    actual_state, actual_seed, actual_result = namespace["end_attempt"](
        deepcopy(terminal_state), deepcopy(reordered), deepcopy(seed_state)
    )
    require(actual_state == expected_state, "Runtime evidence-set replay state mismatch")
    require(actual_result == expected_result, "Runtime evidence-set replay result mismatch")
    require(actual_seed == seed_state, "Runtime evidence-set replay changed exact Seed state")
    require(
        actual_result["code"] == "IDEMPOTENT_REPLAY",
        "Runtime evidence-set order changed identity",
    )
    identity_checks += 1
    require(identity_checks == 5, "Runtime identity sensitivity coverage drift")
    return identity_checks


def check_expression_airgap(profiles_root: Path) -> dict[str, Any]:
    profiles_root = profiles_root.resolve()
    binding = parse_seed_binding()
    expression = profiles_root / "python/aset_runtime_alpha4.py"
    seed_base = profiles_root / "base/seed/python/aset_seed_alpha4.py"
    require(expression.is_file(), "Runtime Python companion missing")
    require(seed_base.is_file(), "exact Seed Python base missing")
    require(
        sha256(seed_base) == binding.companions["PYTHON"][1],
        "Seed Python base byte identity mismatch",
    )
    tree_before = tree_digest(profiles_root)
    _load_expression(seed_base, profiles_root, allowed_imports=frozenset(), allow_seed_loader=False)
    namespace = _load_expression(
        expression,
        profiles_root,
        allowed_imports=frozenset({"hashlib", "copy", "pathlib"}),
        allow_seed_loader=True,
    )
    require(callable(namespace.get("start_attempt")), "generated Runtime start entry point missing")
    require(callable(namespace.get("end_attempt")), "generated Runtime end entry point missing")
    require(
        len(namespace.get("COMPONENT_BINDINGS", [])) == 8,
        "generated Runtime component binding surface drift",
    )
    seed_states = [
        {"subject": "s0", "authority": "a0", "recognition": recognition, "evidence": ("e0",)}
        for recognition in ("UNKNOWN", "ALLOW", "BLOCK")
    ]
    starts = _starts()
    terminals = _terminals()
    states = _states()
    start_checks = 0
    end_checks = 0
    for seed_state in seed_states:
        for state in states:
            for start in starts:
                expected_state, expected_result = _expected_start(state, start)
                actual_state, actual_seed, actual_result = namespace["start_attempt"](
                    deepcopy(state), deepcopy(start), deepcopy(seed_state)
                )
                require(actual_state == expected_state, "generated Runtime start state mismatch")
                require(actual_result == expected_result, "generated Runtime start result mismatch")
                require(actual_seed == seed_state, "Runtime start changed exact Seed state")
                start_checks += 1
            for terminal in terminals:
                expected_state, expected_result = _expected_end(state, terminal)
                actual_state, actual_seed, actual_result = namespace["end_attempt"](
                    deepcopy(state), deepcopy(terminal), deepcopy(seed_state)
                )
                require(actual_state == expected_state, "generated Runtime end state mismatch")
                require(actual_result == expected_result, "generated Runtime end result mismatch")
                require(actual_seed == seed_state, "Runtime end changed exact Seed state")
                end_checks += 1
    identity_checks = _check_identity_sensitivity(namespace, seed_states[0])
    require(
        tree_digest(profiles_root) == tree_before,
        "Runtime profile tree changed during air-gap verification",
    )
    return {
        "document_type": "aset-runtime-python-airgap-evidence",
        "schema_version": 1,
        "semantic_precedence": "NONE",
        "semantic_source_runtime_dependency": "NONE",
        "generator_runtime_dependency": "NONE",
        "companion_import_surface": "RESTRICTED",
        "companion_file_access": "MATERIALIZED_PROFILE_TREE_READ_ONLY",
        "seed_base": {"sha256": sha256(seed_base), "status": "EXACT"},
        "profile_tree_digest": tree_before,
        "cases": {
            "start": start_checks,
            "end": end_checks,
            "total": start_checks + end_checks,
            "identity_sensitivity": identity_checks,
            "grand_total": start_checks + end_checks + identity_checks,
        },
        "seed_states_checked": ["UNKNOWN", "ALLOW", "BLOCK"],
        "evidence_set_order_checks": 1,
        "seed_projection": "STUTTER",
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles-root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist/runtime-python-airgap-evidence.json",
    )
    args = parser.parse_args()
    try:
        evidence = check_expression_airgap(args.profiles_root)
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        cases = evidence["cases"]
        print(f"ALPHA4_RUNTIME_PYTHON_AIRGAP_START={cases['start']}/{cases['start']} PASS")
        print(f"ALPHA4_RUNTIME_PYTHON_AIRGAP_END={cases['end']}/{cases['end']} PASS")
        print(f"ALPHA4_RUNTIME_PYTHON_AIRGAP_TOTAL={cases['total']}/{cases['total']} PASS")
        print(
            "ALPHA4_RUNTIME_PYTHON_AIRGAP_IDENTITY_SENSITIVITY="
            f"{cases['identity_sensitivity']}/5 PASS"
        )
        print(f"ALPHA4_RUNTIME_PYTHON_AIRGAP_GRAND_TOTAL={cases['grand_total']}/7265 PASS")
        print("ALPHA4_RUNTIME_PYTHON_COMPANION_RUNTIME_ISOLATION=PASS")
        print(
            "ALPHA4_RUNTIME_PYTHON_EVIDENCE_SET_ORDER="
            f"{evidence['evidence_set_order_checks']}/{evidence['evidence_set_order_checks']} PASS"
        )
        print("ALPHA4_RUNTIME_PYTHON_SEED_BASE=EXACT")
        print("ALPHA4_RUNTIME_PYTHON_SEED_PROJECTION=STUTTER")
        print("ALPHA4_RUNTIME_PYTHON_SEMANTIC_SOURCE_DEPENDENCY=NONE")
        print("ALPHA4_RUNTIME_PYTHON_GENERATOR_DEPENDENCY=NONE")
        print("ALPHA4_RUNTIME_PYTHON_PROFILE_TREE_UNCHANGED=PASS")
        print("ALPHA4_RUNTIME_PYTHON_AIRGAP=PASS")
        return 0
    except (OSError, ValueError, AirgapError) as error:
        print(f"ALPHA4_RUNTIME_PYTHON_AIRGAP_ERROR={error}")
        print("ALPHA4_RUNTIME_PYTHON_AIRGAP=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
