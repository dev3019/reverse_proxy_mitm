from guardian_client import GuardianScores

THRESHOLD = 0.7


class PolicyEngine:
    @staticmethod
    def evaluate(scores: GuardianScores) -> (bool, str):
        """
        Returns True → ALLOW
        Returns False → BLOCK
        """

        # Pick the highest-scoring category among the three requested constraints.
        categories = {
            "violence": (scores.violence, "description of violent acts"),
            "illegal": (scores.illegal, "inquiries on how to perform an illegal activity"),
            "sexual": (scores.sexual, "sexual content"),
        }

        _, (top_score, top_reason) = max(categories.items(), key=lambda pair: pair[1][0])
        if top_score >= THRESHOLD:
            return (False, top_reason)

        if scores.toxicity >= THRESHOLD:
            return (False, "toxic content")

        return (True, "The prompt is allowed")
