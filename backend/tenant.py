from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TenantConfig:
    id: str
    name: str
    browser_profile: str
    enabled: bool = True


class TenantManager:
    def __init__(self):
        self.tenants: Dict[str, TenantConfig] = {}

    def register(self, tenant_id: str, name: str, browser_profile: str) -> TenantConfig:
        tenant = TenantConfig(id=tenant_id, name=name, browser_profile=browser_profile)
        self.tenants[tenant_id] = tenant
        return tenant

    def get(self, tenant_id: str) -> Optional[TenantConfig]:
        return self.tenants.get(tenant_id)


tenant_manager = TenantManager()

# default tenant for first SaaS rollout
tenant_manager.register("default", "Cliente Padrão", "perfil_playwright/default")
