"""engine/claims/condition_ir/ir.py · 条件 IR 求值（契约 23 §二/§三/§五）。

三值逻辑：True / False / None(unknown)。unknown 不得折叠成 False 或 True。
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from engine.claims.condition_ir.atoms import ATOMS, SIGNATURES, AtomResult, Value

ADDR_RE = re.compile(r"^(?:[YMDH]\.[sb]|DY\d+\.[sb]|LN\d{4}\.[sb]|e\d{3}|\$[A-Za-z_]\w*)$")
FRAMEWORK_DEPS = ("standalone", "requires_school_frame", "requires_pair")


@dataclass
class Outcome:
    value: Value
    bindings: dict[str, str] = field(default_factory=dict)
    failed: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.value is True


def _label(node: dict) -> str:
    name = node.get("atom", "?")
    args = node.get("args") or {}
    if not args:
        return f"{name}()"
    return f"{name}({', '.join(f'{k}={v}' for k, v in args.items())})"


def _resolve(value: Any, env: dict[str, str]) -> tuple[Any, Optional[str]]:
    if isinstance(value, str) and value.startswith("$"):
        var = value[1:]
        if var in env:
            return env[var], None
        return None, f"变量 ${var} 未绑定"
    if isinstance(value, list):
        out = []
        for v in value:
            r, err = _resolve(v, env)
            if err:
                return None, err
            out.append(r)
        return out, None
    return value, None


def evaluate(node: Optional[dict], ctx: dict, env: Optional[dict[str, str]] = None) -> Outcome:
    env = dict(env or {})
    if node is None:
        return Outcome(True, dict(env))
    if not isinstance(node, dict):
        return Outcome(None, {}, unknowns=["条件节点不是对象"])

    if "all" in node:
        cur = dict(env)
        failed: list[str] = []
        unknowns: list[str] = []
        for child in node["all"]:
            out = evaluate(child, ctx, cur)
            cur.update(out.bindings)
            if out.value is False:
                return Outcome(False, cur, failed + out.failed + [_label(child)], out.unknowns)
            if out.value is None:
                unknowns += out.unknowns + [_label(child)]
        if unknowns:
            return Outcome(None, cur, failed, unknowns)
        return Outcome(True, cur)

    if "any" in node:
        unknowns: list[str] = []
        for child in node["any"]:
            out = evaluate(child, ctx, dict(env))
            if out.value is True:
                return out
            if out.value is None:
                unknowns += out.unknowns + [_label(child)]
        if unknowns:
            return Outcome(None, {}, unknowns=unknowns)
        return Outcome(False, {}, failed=[_label(c) for c in node["any"]])

    if "not" in node:
        out = evaluate(node["not"], ctx, dict(env))
        if out.value is None:
            return Outcome(None, {}, unknowns=out.unknowns)
        return Outcome(not out.value, {}, failed=out.failed)

    name = node.get("atom")
    fn = ATOMS.get(name)
    if fn is None:
        return Outcome(None, {}, unknowns=[f"未知原子 {name!r}"])

    args = copy.deepcopy(node.get("args") or {})
    for key, val in list(args.items()):
        resolved, err = _resolve(val, env)
        if err:
            return Outcome(None, {}, unknowns=[f"{_label(node)}: {err}"])
        args[key] = resolved

    res: AtomResult = fn(ctx, args)
    bindings = dict(res.bindings)
    if res.value is True:
        # 原子可自行发布具名绑定（如 zuogong 的 Z/T），供后续 $Z/$T 引用
        for key, val in bindings.items():
            if key in ("addr", "edge_id", "bind") or not isinstance(val, str):
                continue
            env[key] = val
    alias = node.get("as")
    if alias and res.value is True:
        bound = bindings.get("addr") or bindings.get("edge_id")
        if bound:
            env[alias] = bound
            bindings = {alias: bound}
        else:
            return Outcome(None, {}, unknowns=[f"{_label(node)}: as={alias} 无可绑定值"])
    if res.value is False:
        return Outcome(False, {}, failed=[_label(node)])
    if res.value is None:
        return Outcome(None, {}, unknowns=[f"{_label(node)}: {res.note}"])
    return Outcome(True, bindings)


# ------------------------------------------------------------------ 断语求值

def evaluate_claim(claim: dict, ctx: dict) -> dict[str, Any]:
    spec = claim.get("conditions_v2") or {}
    out: dict[str, Any] = {
        "claim_id": claim.get("id"),
        "state": None,
        "value": None,
        "bindings": {},
        "failed_atoms": [],
        "unknown_facts": [],
        "near_miss": [],
        "framework": {"dependency": spec.get("framework_dependency", "requires_school_frame"),
                      "verdict": "pass"},
    }

    inv = evaluate(spec.get("invalidators"), ctx)
    if inv.value is True:
        out.update(state="rejected", value=False, failed_atoms=inv.failed,
                   near_miss=inv.failed)
        out["reason"] = "invalidator 成立"
        return out

    pre = evaluate(spec.get("preconditions"), ctx)
    out.update(value=pre.value, bindings=pre.bindings,
               failed_atoms=pre.failed, unknown_facts=pre.unknowns, near_miss=pre.failed)

    if pre.value is False:
        out["state"] = "rejected"
        out["reason"] = "preconditions 不成立"
        return out
    if pre.value is None:
        out["state"] = "needs_fact"
        out["reason"] = "preconditions 含未知"
        return out

    dep = out["framework"]["dependency"]
    if dep == "requires_pair":
        pair = (spec.get("pair_with") or [None])[0]
        cited = (ctx.get("cited") or {}).get(pair)
        if cited is None:
            out["framework"]["verdict"] = "unknown"
            out["state"] = "evidence_only"
            out["reason"] = f"配对命题 {pair} 未裁决"
            return out
        if cited is not True:
            out["framework"]["verdict"] = "reject"
            out["state"] = "rejected"
            out["reason"] = f"配对命题 {pair} 未成立"
            return out
    elif dep == "requires_school_frame":
        frame = spec.get("frame_atom")
        if not frame:
            out["framework"]["verdict"] = "unknown"
            out["state"] = "evidence_only"
            out["reason"] = "缺少 frame_atom（框架前置）"
            return out
        fo = evaluate(frame, ctx)
        if fo.value is not True:
            out["framework"]["verdict"] = "unknown" if fo.value is None else "reject"
            out["state"] = "evidence_only"
            out["reason"] = "框架前置未成立"
            return out
        out["framework"]["frame_detail"] = fo.bindings

    out["state"] = "candidate"
    out["reason"] = "前置条件全部成立"
    return out


# ------------------------------------------------------------------ 编译校验

def validate_claim(claim: dict) -> list[str]:
    errs: list[str] = []
    for key in ("id", "school", "domain", "statement", "source_ref", "falsifier"):
        if not claim.get(key):
            errs.append(f"缺字段 {key}")
    src = claim.get("source_ref") or {}
    if not src.get("path"):
        errs.append("source_ref 缺 path")
    if not isinstance(src.get("line"), int):
        errs.append("source_ref 缺整数 line")

    spec = claim.get("conditions_v2") or {}
    dep = spec.get("framework_dependency", "requires_school_frame")
    if dep not in FRAMEWORK_DEPS:
        errs.append(f"framework_dependency 非法：{dep}")
    if dep == "requires_pair" and not spec.get("pair_with"):
        errs.append("requires_pair 缺 pair_with")
    if dep == "requires_school_frame" and not spec.get("frame_atom"):
        errs.append("requires_school_frame 缺 frame_atom")

    def walk(node, path="preconditions"):
        if node is None:
            return
        if not isinstance(node, dict):
            errs.append(f"{path} 节点不是对象")
            return
        for key in ("all", "any"):
            if key in node:
                for i, child in enumerate(node[key]):
                    walk(child, f"{path}.{key}[{i}]")
                return
        if "not" in node:
            walk(node["not"], f"{path}.not")
            return
        name = node.get("atom")
        if name not in ATOMS:
            errs.append(f"{path}: 未知原子 {name!r}")
            return
        required, optional = SIGNATURES[name]
        args = node.get("args") or {}
        for key in required:
            if key not in args:
                errs.append(f"{path}: {name} 缺参数 {key}")
        for key in args:
            if key not in required and key not in optional:
                errs.append(f"{path}: {name} 不接受参数 {key}")
        if "as" in node and "as" not in optional:
            errs.append(f"{path}: {name} 不支持 as")
        for key, val in args.items():
            if key in ("at", "a", "b") and isinstance(val, str):
                if not ADDR_RE.match(val):
                    errs.append(f"{path}: 地址非法 {val!r}")

    walk(spec.get("preconditions"), "preconditions")
    walk(spec.get("invalidators"), "invalidators")
    frame = spec.get("frame_atom")
    if frame:
        walk(frame, "frame_atom")
    return errs


def compile_claim(claim: dict) -> dict[str, Any]:
    declared = claim.get("compile_state", "compiled")
    if declared in ("needs_human", "uncompilable", "reference_only"):
        return {"claim_id": claim.get("id"), "status": declared,
                "reason": claim.get("compile_note", "")}
    errs = validate_claim(claim)
    if errs:
        return {"claim_id": claim.get("id"), "status": "uncompilable", "errors": errs}
    if declared == "partial":
        return {"claim_id": claim.get("id"), "status": "partial",
                "reason": claim.get("compile_note", "")}
    return {"claim_id": claim.get("id"), "status": "compiled", "errors": []}
