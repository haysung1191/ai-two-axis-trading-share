from __future__ import annotations

from typing import Any

from src.policy.models import PolicyBundle, PolicyCandidateInput, PolicyEvaluationResult, stable_hash


class SidecarPolicyEvaluator:
    def evaluate(
        self,
        *,
        current_ts: int,
        bundle: PolicyBundle,
        candidates: list[PolicyCandidateInput],
    ) -> list[PolicyEvaluationResult]:
        results: list[PolicyEvaluationResult] = []
        for candidate in sorted(candidates, key=lambda item: (item.symbol, item.scanner_score), reverse=False):
            strategy, reasons, decision, delta = self._evaluate_candidate(current_ts=current_ts, bundle=bundle, candidate=candidate)
            hash_payload = {
                "ts": current_ts,
                "bundle_id": bundle.bundle_id,
                "symbol": candidate.symbol,
                "scanner_score": candidate.scanner_score,
                "features": candidate.features,
                "matched_strategy_id": strategy.strategy_id if strategy else None,
                "policy_decision": decision,
                "policy_score_delta": delta,
                "reasons": reasons,
            }
            results.append(
                PolicyEvaluationResult(
                    symbol=candidate.symbol,
                    matched_strategy_id=strategy.strategy_id if strategy else None,
                    policy_decision=decision,
                    policy_score_delta=delta,
                    reasons=tuple(reasons),
                    deterministic_hash=stable_hash(hash_payload),
                )
            )
        return results

    def _evaluate_candidate(
        self,
        *,
        current_ts: int,
        bundle: PolicyBundle,
        candidate: PolicyCandidateInput,
    ) -> tuple[Any, list[str], str, float]:
        matched = None
        reasons: list[str] = []
        decision = "NEUTRAL"
        delta = 0.0
        symbol_scope = candidate.symbol.replace("/", "-")
        for strategy in bundle.strategies:
            if symbol_scope not in strategy.symbol_scope:
                continue
            matched = strategy
            allow_pass = all(self._eval_clause(clause, candidate.features) for clause in strategy.decision_rules.allow_if)
            reject_hit = [clause for clause in strategy.decision_rules.reject_if if self._eval_clause(clause, candidate.features)]
            reasons = sorted(
                [f"allow:{clause}" for clause in strategy.decision_rules.allow_if if allow_pass]
                + [f"reject:{clause}" for clause in reject_hit]
            )
            if reject_hit:
                decision = "SOFT_REJECT"
                delta = 0.0
            elif allow_pass:
                decision = "BOOST"
                delta = float(strategy.decision_rules.boost_score)
            break

        return matched, reasons, decision, delta

    @staticmethod
    def _eval_clause(clause: str, features: dict[str, float]) -> bool:
        for operator in (" >= ", " <= ", " == ", " != ", " > ", " < "):
            if operator in clause:
                left, right = clause.split(operator, 1)
                lhs = float(features.get(left.strip(), 0.0))
                rhs_key = right.strip()
                rhs = float(features.get(rhs_key, rhs_key))
                if operator == " >= ":
                    return lhs >= rhs
                if operator == " <= ":
                    return lhs <= rhs
                if operator == " == ":
                    return lhs == rhs
                if operator == " != ":
                    return lhs != rhs
                if operator == " > ":
                    return lhs > rhs
                if operator == " < ":
                    return lhs < rhs
        raise ValueError(f"Unsupported clause operator: {clause}")
