
import yaml
from pathlib import Path
from typing import Dict, Any, List
import structlog
from app.core.config import settings

logger = structlog.get_logger()

class CrawlerConfig:
    _instance = None
    _blacklist: List[str] = []
    _inference_rules: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CrawlerConfig, cls).__new__(cls)
            cls._instance.load_rules()
        return cls._instance

    def load_rules(self):
        """Loads rules from yaml files in app/rules/."""
        rules_dir = Path(__file__).parent.parent / "rules"
        
        # Load Blacklist
        try:
            with open(rules_dir / "blacklist_patterns.yaml", "r") as f:
                data = yaml.safe_load(f)
                self._blacklist = data.get("blacklist_patterns", [])
            logger.info("config.loaded", file="blacklist_patterns.yaml")
        except Exception as e:
            logger.error("config.load_failed", file="blacklist_patterns.yaml", error=str(e))
            self._blacklist = []

        # Load Inference Rules
        try:
            with open(rules_dir / "inference_rules.yaml", "r") as f:
                data = yaml.safe_load(f)
                self._inference_rules = data.get("inference_rules", {})
            logger.info("config.loaded", file="inference_rules.yaml")
        except Exception as e:
            logger.error("config.load_failed", file="inference_rules.yaml", error=str(e))
            self._inference_rules = {}

    @property
    def settings(self) -> Dict[str, Any]:
        # Return dict to stay compatible with existing usage, or update usage.
        # Returning dict derived from pydantic settings.
        return {
            "user_agent": settings.CRAWLER_USER_AGENT,
            "timeout_ms": settings.CRAWLER_TIMEOUT_MS,
            "render_wait_ms": settings.CRAWLER_RENDER_WAIT_MS
        }

    @property
    def blacklist(self) -> List[str]:
        return self._blacklist

    @property
    def inference_rules(self) -> Dict[str, Any]:
        return self._inference_rules

crawler_config = CrawlerConfig()
