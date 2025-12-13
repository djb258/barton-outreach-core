"""
Configuration Utilities
=======================
Pipeline configuration loading and management.
Reads from environment variables and config files.
"""

import os
import json
import yaml
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str = ""
    port: int = 5432
    database: str = ""
    user: str = ""
    password: str = ""
    ssl_mode: str = "require"

    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return (f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/"
                f"{self.database}?sslmode={self.ssl_mode}")

    def get_connection_dict(self) -> Dict[str, Any]:
        """Get connection parameters as dict."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "sslmode": self.ssl_mode
        }


@dataclass
class ProviderConfig:
    """Configuration for a single provider."""
    name: str
    api_key: str = ""
    enabled: bool = True
    rate_limit: int = 100  # requests per minute
    timeout: int = 30  # seconds
    max_retries: int = 3
    base_url: str = ""
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchingConfig:
    """Matching thresholds and rules per doctrine."""
    # Domain match (GOLD)
    domain_match_score: float = 1.0

    # Exact name match (SILVER)
    exact_match_score: float = 0.95

    # Fuzzy match thresholds (BRONZE)
    fuzzy_high_threshold: float = 0.92  # Match without city guardrail
    fuzzy_low_threshold: float = 0.85   # Match WITH city guardrail

    # Collision detection
    collision_threshold: float = 0.03   # Ambiguous if within this range

    # City guardrail
    require_city_match_below_high: bool = True


@dataclass
class SlotConfig:
    """Company slot vessel configuration."""
    # 11 slot types per doctrine
    slot_types: List[str] = field(default_factory=lambda: [
        "slot_ceo",
        "slot_cfo",
        "slot_chro",
        "slot_hr_manager",
        "slot_benefits_lead",
        "slot_payroll_admin",
        "slot_controller",
        "slot_operations_head",
        "slot_it_admin",
        "slot_office_manager",
        "slot_board_members"  # This is an array slot
    ])

    # Array slots (can hold multiple people)
    array_slots: List[str] = field(default_factory=lambda: ["slot_board_members"])


@dataclass
class OutputConfig:
    """Output file configuration."""
    output_directory: str = "./output"
    generate_csv: bool = True
    generate_jsonl: bool = True
    generate_sql: bool = True
    generate_audit_log: bool = True

    # File names
    matched_companies_file: str = "company_canonical_updated.csv"
    review_queue_file: str = "review_queue.csv"
    unmatched_file: str = "unmatched_company.csv"
    slots_file: str = "company_slots.jsonl"
    audit_file: str = "company_identity_audit.json"


@dataclass
class RetryConfig:
    """Retry and backoff configuration."""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class PipelineConfig:
    """
    Complete pipeline configuration.
    Central configuration object per doctrine.
    """

    # Run identification
    pipeline_run_id: str = ""

    # Database
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    # Provider configurations by tier
    tier_0_providers: List[ProviderConfig] = field(default_factory=list)
    tier_1_providers: List[ProviderConfig] = field(default_factory=list)
    tier_2_providers: List[ProviderConfig] = field(default_factory=list)

    # Matching rules
    matching: MatchingConfig = field(default_factory=MatchingConfig)

    # Slot configuration
    slots: SlotConfig = field(default_factory=SlotConfig)

    # Output settings
    output: OutputConfig = field(default_factory=OutputConfig)

    # Retry settings
    retry: RetryConfig = field(default_factory=RetryConfig)

    # Batch settings
    batch_size: int = 100
    max_concurrent_requests: int = 10

    # Logging settings
    log_level: str = "INFO"
    log_to_file: bool = True
    log_to_database: bool = True
    log_directory: str = "./logs"

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "pipeline_run_id": self.pipeline_run_id,
            "database": self.database.get_connection_dict(),
            "matching": {
                "domain_match_score": self.matching.domain_match_score,
                "exact_match_score": self.matching.exact_match_score,
                "fuzzy_high_threshold": self.matching.fuzzy_high_threshold,
                "fuzzy_low_threshold": self.matching.fuzzy_low_threshold,
                "collision_threshold": self.matching.collision_threshold,
            },
            "slots": {
                "slot_types": self.slots.slot_types,
                "array_slots": self.slots.array_slots,
            },
            "output": {
                "output_directory": self.output.output_directory,
                "generate_csv": self.output.generate_csv,
                "generate_jsonl": self.output.generate_jsonl,
            },
            "batch_size": self.batch_size,
            "log_level": self.log_level,
        }


def load_config(config_path: str = None) -> PipelineConfig:
    """
    Load pipeline configuration from file or environment.

    Priority:
    1. Config file (if specified)
    2. Environment variables
    3. Default values

    Args:
        config_path: Optional path to config file

    Returns:
        Loaded PipelineConfig
    """
    config = PipelineConfig()

    # Try loading from file first
    if config_path and Path(config_path).exists():
        config = load_config_from_file(config_path)

    # Override with environment variables
    config = _apply_env_overrides(config)

    # Validate configuration
    errors = validate_config(config)
    if errors:
        import logging
        for error in errors:
            logging.warning(f"Config validation warning: {error}")

    return config


def load_config_from_env() -> PipelineConfig:
    """
    Load configuration from environment variables.

    Environment variables:
    - NEON_HOST, NEON_PORT, NEON_DATABASE, NEON_USER, NEON_PASSWORD
    - HUNTER_API_KEY, CLEARBIT_API_KEY, APOLLO_API_KEY
    - PROSPEO_API_KEY, SNOV_API_KEY, CLAY_API_KEY
    - PIPELINE_BATCH_SIZE, PIPELINE_LOG_LEVEL

    Returns:
        PipelineConfig from environment
    """
    config = PipelineConfig()
    config = _apply_env_overrides(config)
    return config


def _apply_env_overrides(config: PipelineConfig) -> PipelineConfig:
    """Apply environment variable overrides to config."""

    # Database config
    config.database.host = os.getenv("NEON_HOST", config.database.host)
    config.database.port = int(os.getenv("NEON_PORT", config.database.port))
    config.database.database = os.getenv("NEON_DATABASE", config.database.database)
    config.database.user = os.getenv("NEON_USER", config.database.user)
    config.database.password = os.getenv("NEON_PASSWORD", config.database.password)

    # Tier 0 providers (Free)
    if os.getenv("FIRECRAWL_API_KEY"):
        config.tier_0_providers.append(ProviderConfig(
            name="firecrawl",
            api_key=os.getenv("FIRECRAWL_API_KEY", ""),
            base_url=os.getenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev")
        ))

    # Tier 1 providers (Low cost)
    if os.getenv("HUNTER_API_KEY"):
        config.tier_1_providers.append(ProviderConfig(
            name="hunter",
            api_key=os.getenv("HUNTER_API_KEY", ""),
            base_url="https://api.hunter.io/v2"
        ))

    if os.getenv("CLEARBIT_API_KEY"):
        config.tier_1_providers.append(ProviderConfig(
            name="clearbit",
            api_key=os.getenv("CLEARBIT_API_KEY", ""),
            base_url="https://company.clearbit.com/v2"
        ))

    if os.getenv("APOLLO_API_KEY"):
        config.tier_1_providers.append(ProviderConfig(
            name="apollo",
            api_key=os.getenv("APOLLO_API_KEY", ""),
            base_url="https://api.apollo.io/v1"
        ))

    # Tier 2 providers (Premium)
    if os.getenv("PROSPEO_API_KEY"):
        config.tier_2_providers.append(ProviderConfig(
            name="prospeo",
            api_key=os.getenv("PROSPEO_API_KEY", "")
        ))

    if os.getenv("SNOV_API_KEY"):
        config.tier_2_providers.append(ProviderConfig(
            name="snov",
            api_key=os.getenv("SNOV_API_KEY", "")
        ))

    if os.getenv("CLAY_API_KEY"):
        config.tier_2_providers.append(ProviderConfig(
            name="clay",
            api_key=os.getenv("CLAY_API_KEY", "")
        ))

    # Pipeline settings
    if os.getenv("PIPELINE_BATCH_SIZE"):
        config.batch_size = int(os.getenv("PIPELINE_BATCH_SIZE"))

    if os.getenv("PIPELINE_LOG_LEVEL"):
        config.log_level = os.getenv("PIPELINE_LOG_LEVEL")

    if os.getenv("PIPELINE_OUTPUT_DIR"):
        config.output.output_directory = os.getenv("PIPELINE_OUTPUT_DIR")

    return config


def load_config_from_file(file_path: str) -> PipelineConfig:
    """
    Load configuration from YAML or JSON file.

    Args:
        file_path: Path to config file

    Returns:
        PipelineConfig from file
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {file_path}")

    with open(path, 'r') as f:
        if path.suffix in ['.yaml', '.yml']:
            data = yaml.safe_load(f)
        elif path.suffix == '.json':
            data = json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")

    return _dict_to_config(data)


def _dict_to_config(data: Dict[str, Any]) -> PipelineConfig:
    """Convert dictionary to PipelineConfig."""
    config = PipelineConfig()

    if 'database' in data:
        db = data['database']
        config.database = DatabaseConfig(
            host=db.get('host', ''),
            port=db.get('port', 5432),
            database=db.get('database', ''),
            user=db.get('user', ''),
            password=db.get('password', ''),
            ssl_mode=db.get('ssl_mode', 'require')
        )

    if 'matching' in data:
        m = data['matching']
        config.matching = MatchingConfig(
            fuzzy_high_threshold=m.get('fuzzy_high_threshold', 0.92),
            fuzzy_low_threshold=m.get('fuzzy_low_threshold', 0.85),
            collision_threshold=m.get('collision_threshold', 0.03)
        )

    if 'output' in data:
        o = data['output']
        config.output = OutputConfig(
            output_directory=o.get('output_directory', './output'),
            generate_csv=o.get('generate_csv', True),
            generate_jsonl=o.get('generate_jsonl', True)
        )

    config.batch_size = data.get('batch_size', 100)
    config.log_level = data.get('log_level', 'INFO')

    return config


def get_provider_config(config: PipelineConfig,
                        provider_name: str) -> Optional[ProviderConfig]:
    """
    Get configuration for a specific provider.

    Args:
        config: Pipeline configuration
        provider_name: Name of provider (e.g., 'hunter', 'clearbit')

    Returns:
        ProviderConfig or None if not found
    """
    all_providers = (config.tier_0_providers +
                     config.tier_1_providers +
                     config.tier_2_providers)

    for provider in all_providers:
        if provider.name.lower() == provider_name.lower():
            return provider

    return None


def get_database_config(config: PipelineConfig = None) -> DatabaseConfig:
    """
    Get database configuration.

    If config not provided, loads from environment.

    Args:
        config: Optional PipelineConfig

    Returns:
        DatabaseConfig
    """
    if config:
        return config.database

    return DatabaseConfig(
        host=os.getenv("NEON_HOST", ""),
        port=int(os.getenv("NEON_PORT", 5432)),
        database=os.getenv("NEON_DATABASE", ""),
        user=os.getenv("NEON_USER", ""),
        password=os.getenv("NEON_PASSWORD", ""),
        ssl_mode=os.getenv("NEON_SSL_MODE", "require")
    )


def validate_config(config: PipelineConfig) -> List[str]:
    """
    Validate configuration completeness.

    Checks:
    - Database connection info present
    - Thresholds in valid ranges
    - Output directory exists or can be created

    Args:
        config: Configuration to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check database config
    if not config.database.host:
        errors.append("Database host not configured")
    if not config.database.database:
        errors.append("Database name not configured")

    # Check threshold ranges
    if not 0 <= config.matching.fuzzy_low_threshold <= 1:
        errors.append("fuzzy_low_threshold must be between 0 and 1")
    if not 0 <= config.matching.fuzzy_high_threshold <= 1:
        errors.append("fuzzy_high_threshold must be between 0 and 1")
    if config.matching.fuzzy_low_threshold > config.matching.fuzzy_high_threshold:
        errors.append("fuzzy_low_threshold must be <= fuzzy_high_threshold")

    # Check output directory
    output_dir = Path(config.output.output_directory)
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create output directory: {e}")

    return errors


def save_config(config: PipelineConfig, file_path: str) -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration to save
        file_path: Output file path (.yaml or .json)
    """
    path = Path(file_path)
    data = config.to_dict()

    # Remove sensitive data before saving
    if 'database' in data:
        data['database']['password'] = '***REDACTED***'

    with open(path, 'w') as f:
        if path.suffix in ['.yaml', '.yml']:
            yaml.dump(data, f, default_flow_style=False)
        else:
            json.dump(data, f, indent=2)
