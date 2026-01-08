"""
Pipeline Configuration Utilities
================================
Configuration management for pipeline execution.

Loads configuration from:
1. Environment variables
2. .env file
3. config.yaml file
4. Doppler secrets (if available)
"""

import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class Environment(Enum):
    """Deployment environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ProviderTier(Enum):
    """Provider cost tier."""
    TIER_0 = 0  # Free
    TIER_1 = 1  # Low cost ($0.001-$0.01)
    TIER_2 = 2  # Premium ($0.01-$0.05)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str = ""
    port: int = 5432
    database: str = ""
    user: str = ""
    password: str = ""
    ssl_mode: str = "require"
    pool_size: int = 10
    max_overflow: int = 20

    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"
        )


@dataclass
class ProviderConfig:
    """Configuration for enrichment providers."""
    name: str
    tier: ProviderTier
    api_key: str = ""
    api_url: str = ""
    rate_limit: int = 60  # requests per minute
    timeout: int = 30  # seconds
    max_retries: int = 3
    enabled: bool = True
    cost_per_request: float = 0.0

    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        return bool(self.api_key) and self.enabled


@dataclass
class PhaseConfig:
    """Configuration for a pipeline phase."""
    name: str
    enabled: bool = True
    timeout: int = 300  # seconds
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    fail_hard: bool = True
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BITConfig:
    """
    BIT Engine configuration.

    Per Funnel Doctrine (ctb/sys/doctrine/funnel_rules.md):
    - WARM_THRESHOLD: 25 - Score at which SUSPECT → WARM (outreach eligible)
    - HOT_THRESHOLD: 50 - Score for priority outreach
    - BURNING_THRESHOLD: 75 - Score for immediate action

    State Machine: COLD → SUSPECT → WARM → HOT → BURNING
    """
    warm_threshold: int = 25      # Score for SUSPECT → WARM (outreach eligible)
    hot_threshold: int = 50       # Score for priority outreach
    burning_threshold: int = 75   # Score for immediate action
    decay_enabled: bool = True
    decay_half_life_days: int = 30
    max_score: int = 1000
    min_score: int = 0


@dataclass
class PipelineConfig:
    """Complete pipeline configuration."""
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False

    # Database
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    # Providers
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)

    # Phases
    phases: Dict[str, PhaseConfig] = field(default_factory=dict)

    # BIT Engine
    bit: BITConfig = field(default_factory=BITConfig)

    # General settings
    correlation_id_required: bool = True
    hub_gate_required: bool = True
    signal_dedup_enabled: bool = True

    # Output settings
    output_dir: str = "output"
    log_level: str = "INFO"

    # Rate limiting
    global_rate_limit: int = 100  # requests per minute across all providers

    # Cost caps
    max_cost_per_record: float = 0.10  # USD
    max_daily_cost: float = 100.0  # USD


# =============================================================================
# PROVIDER DEFAULTS
# =============================================================================

DEFAULT_PROVIDERS = {
    # Tier 0: Free
    "firecrawl": ProviderConfig(
        name="firecrawl",
        tier=ProviderTier.TIER_0,
        api_url="https://api.firecrawl.dev",
        cost_per_request=0.0001
    ),
    "google_places": ProviderConfig(
        name="google_places",
        tier=ProviderTier.TIER_0,
        api_url="https://maps.googleapis.com/maps/api/place",
        cost_per_request=0.003
    ),
    "web_scraper": ProviderConfig(
        name="web_scraper",
        tier=ProviderTier.TIER_0,
        cost_per_request=0.0
    ),

    # Tier 1: Low cost
    "hunter": ProviderConfig(
        name="hunter",
        tier=ProviderTier.TIER_1,
        api_url="https://api.hunter.io/v2",
        cost_per_request=0.008
    ),
    "clearbit": ProviderConfig(
        name="clearbit",
        tier=ProviderTier.TIER_1,
        api_url="https://company.clearbit.com/v2",
        cost_per_request=0.01
    ),
    "apollo": ProviderConfig(
        name="apollo",
        tier=ProviderTier.TIER_1,
        api_url="https://api.apollo.io/v1",
        cost_per_request=0.005
    ),

    # Tier 2: Premium
    "prospeo": ProviderConfig(
        name="prospeo",
        tier=ProviderTier.TIER_2,
        api_url="https://api.prospeo.io",
        cost_per_request=0.003
    ),
    "snov": ProviderConfig(
        name="snov",
        tier=ProviderTier.TIER_2,
        api_url="https://api.snov.io/v1",
        cost_per_request=0.004
    ),
    "clay": ProviderConfig(
        name="clay",
        tier=ProviderTier.TIER_2,
        api_url="https://api.clay.com/v1",
        cost_per_request=0.01
    ),
}

DEFAULT_PHASES = {
    "phase1": PhaseConfig(name="company_matching", batch_size=500),
    "phase2": PhaseConfig(name="domain_resolution", batch_size=200),
    "phase3": PhaseConfig(name="email_pattern_waterfall", batch_size=100),
    "phase4": PhaseConfig(name="pattern_verification", batch_size=100),
    "phase0": PhaseConfig(name="people_ingest", batch_size=500),
    "phase5": PhaseConfig(name="email_generation", batch_size=200),
    "phase6": PhaseConfig(name="slot_assignment", batch_size=500),
    "phase7": PhaseConfig(name="enrichment_queue", batch_size=100),
    "phase8": PhaseConfig(name="output_writer", batch_size=1000),
}


# =============================================================================
# CONFIGURATION LOADER
# =============================================================================

_config: Optional[PipelineConfig] = None


def load_config(
    config_path: str = None,
    env_prefix: str = "PIPELINE_"
) -> PipelineConfig:
    """
    Load pipeline configuration.

    Priority (highest to lowest):
    1. Environment variables
    2. Config file (YAML/JSON)
    3. Default values

    Args:
        config_path: Path to config file (optional)
        env_prefix: Prefix for environment variables

    Returns:
        PipelineConfig instance
    """
    global _config

    if _config is not None:
        return _config

    config = PipelineConfig()

    # Load from file if provided
    if config_path:
        config = _load_from_file(config_path, config)

    # Override with environment variables
    config = _load_from_env(config, env_prefix)

    # Load database config
    config.database = _load_database_config()

    # Load provider configs
    config.providers = _load_provider_configs()

    # Load phase configs
    config.phases = DEFAULT_PHASES.copy()

    # Load BIT config
    config.bit = _load_bit_config()

    _config = config
    return config


def _load_from_file(path: str, config: PipelineConfig) -> PipelineConfig:
    """Load configuration from file."""
    file_path = Path(path)

    if not file_path.exists():
        logger.warning(f"Config file not found: {path}")
        return config

    try:
        if file_path.suffix in ['.yaml', '.yml']:
            import yaml
            with open(file_path) as f:
                data = yaml.safe_load(f)
        elif file_path.suffix == '.json':
            with open(file_path) as f:
                data = json.load(f)
        else:
            logger.warning(f"Unknown config file format: {file_path.suffix}")
            return config

        # Update config from file data
        if 'environment' in data:
            config.environment = Environment(data['environment'])
        if 'debug' in data:
            config.debug = data['debug']
        if 'output_dir' in data:
            config.output_dir = data['output_dir']
        if 'log_level' in data:
            config.log_level = data['log_level']

    except Exception as e:
        logger.error(f"Error loading config file: {e}")

    return config


def _load_from_env(config: PipelineConfig, prefix: str) -> PipelineConfig:
    """Load configuration from environment variables."""
    # Environment
    env = os.getenv(f"{prefix}ENVIRONMENT", os.getenv("ENVIRONMENT", "development"))
    try:
        config.environment = Environment(env.lower())
    except ValueError:
        pass

    # Debug mode
    config.debug = os.getenv(f"{prefix}DEBUG", "false").lower() == "true"

    # Output directory
    config.output_dir = os.getenv(f"{prefix}OUTPUT_DIR", config.output_dir)

    # Log level
    config.log_level = os.getenv(f"{prefix}LOG_LEVEL", config.log_level)

    return config


def _load_database_config() -> DatabaseConfig:
    """Load database configuration from environment."""
    return DatabaseConfig(
        host=os.getenv("NEON_HOST", ""),
        port=int(os.getenv("NEON_PORT", "5432")),
        database=os.getenv("NEON_DATABASE", ""),
        user=os.getenv("NEON_USER", ""),
        password=os.getenv("NEON_PASSWORD", ""),
        ssl_mode=os.getenv("NEON_SSL_MODE", "require"),
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
    )


def _load_provider_configs() -> Dict[str, ProviderConfig]:
    """Load provider configurations from environment."""
    providers = DEFAULT_PROVIDERS.copy()

    # Override API keys from environment
    api_key_map = {
        "firecrawl": "FIRECRAWL_API_KEY",
        "google_places": "GOOGLE_API_KEY",
        "hunter": "HUNTER_API_KEY",
        "clearbit": "CLEARBIT_API_KEY",
        "apollo": "APOLLO_API_KEY",
        "prospeo": "PROSPEO_API_KEY",
        "snov": "SNOV_API_KEY",
        "clay": "CLAY_API_KEY",
    }

    for provider_name, env_var in api_key_map.items():
        if provider_name in providers:
            api_key = os.getenv(env_var, "")
            providers[provider_name].api_key = api_key
            providers[provider_name].enabled = bool(api_key)

    return providers


def _load_bit_config() -> BITConfig:
    """
    Load BIT Engine configuration from environment.

    Per Funnel Doctrine: WARM=25, HOT=50, BURNING=75
    """
    return BITConfig(
        warm_threshold=int(os.getenv("BIT_WARM_THRESHOLD", "25")),
        hot_threshold=int(os.getenv("BIT_HOT_THRESHOLD", "50")),
        burning_threshold=int(os.getenv("BIT_BURNING_THRESHOLD", "75")),
        decay_enabled=os.getenv("BIT_DECAY_ENABLED", "true").lower() == "true",
        decay_half_life_days=int(os.getenv("BIT_DECAY_HALF_LIFE", "30")),
        max_score=int(os.getenv("BIT_MAX_SCORE", "1000")),
        min_score=int(os.getenv("BIT_MIN_SCORE", "0")),
    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_config() -> PipelineConfig:
    """Get current configuration (loads if not already loaded)."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_provider_config(provider_name: str) -> Optional[ProviderConfig]:
    """
    Get configuration for a specific provider.

    Args:
        provider_name: Name of the provider

    Returns:
        ProviderConfig or None if not found
    """
    config = get_config()
    return config.providers.get(provider_name.lower())


def get_database_config() -> DatabaseConfig:
    """Get database configuration."""
    config = get_config()
    return config.database


def get_phase_config(phase_name: str) -> Optional[PhaseConfig]:
    """
    Get configuration for a specific phase.

    Args:
        phase_name: Name of the phase

    Returns:
        PhaseConfig or None if not found
    """
    config = get_config()
    return config.phases.get(phase_name)


def get_bit_config() -> BITConfig:
    """Get BIT Engine configuration."""
    config = get_config()
    return config.bit


def get_enabled_providers(tier: ProviderTier = None) -> List[ProviderConfig]:
    """
    Get list of enabled providers.

    Args:
        tier: Optional tier filter

    Returns:
        List of enabled ProviderConfig objects
    """
    config = get_config()
    providers = [p for p in config.providers.values() if p.is_configured()]

    if tier is not None:
        providers = [p for p in providers if p.tier == tier]

    return sorted(providers, key=lambda p: p.tier.value)


def is_production() -> bool:
    """Check if running in production environment."""
    config = get_config()
    return config.environment == Environment.PRODUCTION


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    config = get_config()
    return config.debug


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "Environment",
    "ProviderTier",
    # Data classes
    "DatabaseConfig",
    "ProviderConfig",
    "PhaseConfig",
    "BITConfig",
    "PipelineConfig",
    # Main functions
    "load_config",
    "get_config",
    "get_provider_config",
    "get_database_config",
    "get_phase_config",
    "get_bit_config",
    "get_enabled_providers",
    # Convenience functions
    "is_production",
    "is_debug",
]
