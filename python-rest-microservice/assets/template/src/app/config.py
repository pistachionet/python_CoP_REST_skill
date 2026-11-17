"""Settings come from environment variables only, so any platform can configure the service."""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    service_name: str = field(default_factory=lambda: os.getenv("SERVICE_NAME", "example-service"))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "local"))
