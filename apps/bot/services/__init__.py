from .backend_client import BackendClient
from .deduplicator import MessageDeduplicator
from .matcher import MatchResult, match_message
from .normalizer import normalize_text
from .rules_cache import RulesCache

__all__ = [
    "BackendClient",
    "MessageDeduplicator",
    "MatchResult",
    "match_message",
    "normalize_text",
    "RulesCache",
]
