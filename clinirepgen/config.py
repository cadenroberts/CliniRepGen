"""
Configuration - Default settings and environment variable handling.

Settings can be configured via:
1. Environment variables
2. Config file (config.yaml or config.json)
3. CLI arguments
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


@dataclass
class LLMConfig:
    """LLM configuration."""
    model: str = field(default_factory=lambda: os.getenv("CLINIREPGEN_MODEL", "gpt-4o"))
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("API_KEY"))
    api_base: str = field(default_factory=lambda: os.getenv("API_BASE", "https://api.openai.com/v1"))
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout: float = 300.0


@dataclass
class PipelineSettings:
    """Pipeline settings."""
    max_iterations: int = 3
    min_score_to_pass: float = 70.0
    strict_validation: bool = False
    report_types: list = field(default_factory=lambda: ["consort", "ich_e3"])


@dataclass
class OutputSettings:
    """Output settings."""
    output_dir: str = "output"
    save_intermediate: bool = True
    output_format: str = "markdown"  # markdown, json, html


@dataclass
class Config:
    """Main configuration class."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    pipeline: PipelineSettings = field(default_factory=PipelineSettings)
    output: OutputSettings = field(default_factory=OutputSettings)

    @classmethod
    def from_file(cls, path: str) -> "Config":
        """Load configuration from a file."""
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        if path.suffix in ['.yaml', '.yml']:
            with open(path) as f:
                data = yaml.safe_load(f)
        elif path.suffix == '.json':
            with open(path) as f:
                data = json.load(f)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        config = cls()

        if 'llm' in data:
            for key, value in data['llm'].items():
                if hasattr(config.llm, key):
                    setattr(config.llm, key, value)

        if 'pipeline' in data:
            for key, value in data['pipeline'].items():
                if hasattr(config.pipeline, key):
                    setattr(config.pipeline, key, value)

        if 'output' in data:
            for key, value in data['output'].items():
                if hasattr(config.output, key):
                    setattr(config.output, key, value)

        return config

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        config = cls()

        # LLM settings
        if os.getenv("CLINIREPGEN_MODEL"):
            config.llm.model = os.getenv("CLINIREPGEN_MODEL")
        if os.getenv("API_KEY"):
            config.llm.api_key = os.getenv("API_KEY")
        if os.getenv("API_BASE"):
            config.llm.api_base = os.getenv("API_BASE")
        if os.getenv("CLINIREPGEN_TEMPERATURE"):
            config.llm.temperature = float(os.getenv("CLINIREPGEN_TEMPERATURE"))

        # Pipeline settings
        if os.getenv("CLINIREPGEN_MAX_ITERATIONS"):
            config.pipeline.max_iterations = int(os.getenv("CLINIREPGEN_MAX_ITERATIONS"))
        if os.getenv("CLINIREPGEN_STRICT"):
            config.pipeline.strict_validation = os.getenv("CLINIREPGEN_STRICT").lower() == "true"

        # Output settings
        if os.getenv("CLINIREPGEN_OUTPUT_DIR"):
            config.output.output_dir = os.getenv("CLINIREPGEN_OUTPUT_DIR")

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'llm': {
                'model': self.llm.model,
                'api_base': self.llm.api_base,
                'temperature': self.llm.temperature,
                'max_tokens': self.llm.max_tokens,
            },
            'pipeline': {
                'max_iterations': self.pipeline.max_iterations,
                'min_score_to_pass': self.pipeline.min_score_to_pass,
                'strict_validation': self.pipeline.strict_validation,
                'report_types': self.pipeline.report_types,
            },
            'output': {
                'output_dir': self.output.output_dir,
                'save_intermediate': self.output.save_intermediate,
                'output_format': self.output.output_format,
            }
        }

    def save(self, path: str) -> None:
        """Save configuration to file."""
        path = Path(path)
        data = self.to_dict()

        if path.suffix in ['.yaml', '.yml']:
            with open(path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        else:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)


# Default config instance
default_config = Config.from_env()


def get_config(config_path: Optional[str] = None) -> Config:
    """Get configuration, optionally loading from file."""
    if config_path:
        return Config.from_file(config_path)

    # Check for default config files
    for default_path in ['config.yaml', 'config.yml', 'config.json', 'clinirepgen.yaml']:
        if Path(default_path).exists():
            return Config.from_file(default_path)

    return Config.from_env()
