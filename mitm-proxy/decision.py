from guardian_client import GuardianScores
from policy import PolicyEngine

class Decision:
    def __init__(self, allow: bool, reason: str = ""):
        self.allow = allow
        self.reason = reason

class DecisionEngine:
    @staticmethod
    def decide(scores: GuardianScores) -> Decision:
        print(scores)
        allowed, reason = PolicyEngine.evaluate(scores)

        if allowed:
            return Decision(True)

        return Decision(allowed, reason=reason)