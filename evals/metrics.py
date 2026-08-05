"""Metric implementations shared by all runners. Pure functions over plain lists — no I/O,
no imports from the app, so they are trivially unit-testable and provider-independent."""

from __future__ import annotations

from collections import defaultdict


def recall_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """Fraction of the relevant docs that appear in the top-k retrieved."""
    rel = set(relevant)
    if not rel:
        return 1.0
    topk = set(retrieved[:k])
    return len(topk & rel) / len(rel)


def precision_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """Fraction of the top-k retrieved that are relevant."""
    rel = set(relevant)
    topk = retrieved[:k]
    if not topk:
        return 0.0
    hits = sum(1 for d in topk if d in rel)
    return hits / min(k, len(topk))


def accuracy(y_true: list[str], y_pred: list[str]) -> float:
    if not y_true:
        return 0.0
    correct = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == p)
    return correct / len(y_true)


def per_class_f1(y_true: list[str], y_pred: list[str], labels: list[str] | None = None) -> dict:
    """Return {label: {precision, recall, f1, support}} plus a 'macro_f1' key."""
    labels = labels or sorted(set(y_true) | set(y_pred))
    out: dict = {}
    f1s: list[float] = []
    for lab in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == lab and p == lab)
        fp = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t != lab and p == lab)
        fn = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == lab and p != lab)
        support = sum(1 for t in y_true if t == lab)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        out[lab] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "support": support,
        }
        if support:
            f1s.append(f1)
    out["macro_f1"] = round(sum(f1s) / len(f1s), 3) if f1s else 0.0
    return out


def confusion_matrix(y_true: list[str], y_pred: list[str], labels: list[str] | None = None) -> dict:
    labels = labels or sorted(set(y_true) | set(y_pred))
    matrix: dict[str, dict[str, int]] = {t: defaultdict(int) for t in labels}
    for t, p in zip(y_true, y_pred, strict=False):
        matrix.setdefault(t, defaultdict(int))
        matrix[t][p] += 1
    return {t: dict(row) for t, row in matrix.items()}


def escalation_recall(results: list[dict]) -> float:
    """results: [{must_escalate: bool, escalated: bool}]. Recall over the must-escalate set."""
    must = [r for r in results if r.get("must_escalate")]
    if not must:
        return 1.0
    caught = sum(1 for r in must if r.get("escalated"))
    return caught / len(must)


def citation_coverage(turns: list[dict]) -> float:
    """turns: [{answered: bool, has_citation: bool}]. Fraction of answered turns that cite."""
    answered = [t for t in turns if t.get("answered")]
    if not answered:
        return 1.0
    cited = sum(1 for t in answered if t.get("has_citation"))
    return cited / len(answered)
