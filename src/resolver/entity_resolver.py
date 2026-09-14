import re
import logging
import difflib
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Common corporate suffixes to normalize
COMPANY_SUFFIXES_REGEX = re.compile(
    r'\b(inc|incorporated|llc|corp|corporation|co|company|ltd|limited|gmbh|plc|pvt)\b[\.]?',
    re.IGNORECASE
)

# Known canonical alias lookup map
DEFAULT_ALIASES: Dict[str, str] = {
    "open ai": "OpenAI",
    "openai": "OpenAI",
    "openai inc": "OpenAI",
    "google deepmind": "Google DeepMind",
    "deepmind": "Google DeepMind",
    "meta ai": "Meta AI",
    "anthropic pbc": "Anthropic",
    "anthropic": "Anthropic",
    "mistral ai": "Mistral AI",
    "mistral": "Mistral AI",
}


@dataclass
class ResolutionResult:
    raw_name: str
    canonical_name: str
    entity_type: str
    source_url: Optional[str]
    resolution_method: str  # "exact", "alias", "normalized", "fuzzy", "unresolved"
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_name": self.raw_name,
            "canonical_name": self.canonical_name,
            "entity_type": self.entity_type,
            "source_url": self.source_url,
            "resolution_method": self.resolution_method,
            "confidence": self.confidence,
        }


def normalize_entity_name(raw_name: str) -> str:
    """
    Deterministically normalize company/entity name.
    - Strips punctuation and corporate suffixes
    - Collapses extra whitespace
    - Lowercases text
    """
    if not raw_name or not isinstance(raw_name, str):
        return ""

    text = raw_name.strip().lower()
    # Remove punctuation except alphanumeric and space
    text = re.sub(r'[^\w\s]', '', text)
    # Remove corporate suffixes
    text = COMPANY_SUFFIXES_REGEX.sub('', text)
    # Collapse spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class EntityResolver:
    """Deterministic entity resolver with fuzzy matching fallback and resolution logging."""

    def __init__(self, aliases: Optional[Dict[str, str]] = None, fuzzy_threshold: float = 0.85):
        self.aliases = aliases if aliases is not None else DEFAULT_ALIASES
        self.fuzzy_threshold = fuzzy_threshold

    def resolve(
        self,
        raw_name: str,
        entity_type: str,
        known_canonical_names: List[str],
        source_url: Optional[str] = None,
    ) -> ResolutionResult:
        if not raw_name or not raw_name.strip():
            return ResolutionResult(
                raw_name=raw_name or "",
                canonical_name="Unknown",
                entity_type=entity_type,
                source_url=source_url,
                resolution_method="unresolved",
                confidence=0.0,
            )

        clean_raw = raw_name.strip()
        norm_raw = normalize_entity_name(clean_raw)

        # 1. Alias match lookup
        if norm_raw in self.aliases:
            canonical = self.aliases[norm_raw]
            logger.info(f"Resolved entity via alias: '{clean_raw}' -> '{canonical}' (confidence: 1.0)")
            return ResolutionResult(
                raw_name=clean_raw,
                canonical_name=canonical,
                entity_type=entity_type,
                source_url=source_url,
                resolution_method="alias",
                confidence=1.0,
            )

        # 2. Exact normalized match against known canonical list
        for canonical in known_canonical_names:
            norm_canonical = normalize_entity_name(canonical)
            if norm_raw == norm_canonical:
                logger.info(f"Resolved entity via normalization: '{clean_raw}' -> '{canonical}' (confidence: 1.0)")
                return ResolutionResult(
                    raw_name=clean_raw,
                    canonical_name=canonical,
                    entity_type=entity_type,
                    source_url=source_url,
                    resolution_method="normalized",
                    confidence=1.0,
                )

        # 3. Fuzzy ratio match
        best_match = None
        highest_score = 0.0

        for canonical in known_canonical_names:
            norm_canonical = normalize_entity_name(canonical)
            ratio = difflib.SequenceMatcher(None, norm_raw, norm_canonical).ratio()
            if ratio > highest_score:
                highest_score = ratio
                best_match = canonical

        if best_match and highest_score >= self.fuzzy_threshold:
            logger.info(f"Resolved entity via fuzzy match ({highest_score:.2f}): '{clean_raw}' -> '{best_match}'")
            return ResolutionResult(
                raw_name=clean_raw,
                canonical_name=best_match,
                entity_type=entity_type,
                source_url=source_url,
                resolution_method="fuzzy",
                confidence=round(highest_score, 2),
            )

        # 4. Low-confidence match fallback
        if best_match:
            logger.warning(
                f"Low-confidence entity match logged for review: '{clean_raw}' -> candidate '{best_match}' "
                f"(score: {highest_score:.2f} < threshold: {self.fuzzy_threshold})"
            )

        return ResolutionResult(
            raw_name=clean_raw,
            canonical_name=clean_raw,  # Preserve raw name as canonical when confidence is low
            entity_type=entity_type,
            source_url=source_url,
            resolution_method="unresolved",
            confidence=0.5 if best_match else 0.0,
        )
