"""
Module Registry for Tier 2 Domain Vertical Modules

Provides dynamic module loading, enable/disable functionality, and dependency management.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ModuleStatus(str, Enum):
    """Module activation status"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class ModuleInfo:
    """Module metadata"""
    module_id: str
    name: str
    description: str
    version: str
    tier: int  # 2 or 3
    category: str  # e.g., "document_intelligence", "construction", etc.
    dependencies: List[str]  # List of tier_1 services required
    status: ModuleStatus
    routes_prefix: str  # e.g., "/api/v1/modules/docu-extract"
    
    
class ModuleRegistry:
    """
    Dynamic module registry for pluggable domain vertical modules.
    
    Features:
    - Register/unregister modules
    - Enable/disable modules
    - Dependency validation
    - Lifecycle management
    """
    
    def __init__(self):
        self._modules: Dict[str, ModuleInfo] = {}
        self._loaded_routers: Dict[str, Any] = {}
        logger.info("Module registry initialized")
    
    def register(
        self,
        module_id: str,
        name: str,
        description: str,
        version: str,
        tier: int,
        category: str,
        dependencies: List[str],
        routes_prefix: str
    ) -> None:
        """Register a new module"""
        module_info = ModuleInfo(
            module_id=module_id,
            name=name,
            description=description,
            version=version,
            tier=tier,
            category=category,
            dependencies=dependencies,
            status=ModuleStatus.DISABLED,  # Default to disabled
            routes_prefix=routes_prefix
        )
        
        self._modules[module_id] = module_info
        logger.info(f"Registered module: {name} (ID: {module_id}, Tier: {tier})")
    
    def enable(self, module_id: str) -> bool:
        """Enable a module"""
        if module_id not in self._modules:
            logger.error(f"Module not found: {module_id}")
            return False
        
        module = self._modules[module_id]
        
        # Validate dependencies
        for dep in module.dependencies:
            # Check if tier_1 service exists
            # TODO: Implement dependency validation
            pass
        
        module.status = ModuleStatus.ENABLED
        logger.info(f"Enabled module: {module.name}")
        return True
    
    def disable(self, module_id: str) -> bool:
        """Disable a module"""
        if module_id not in self._modules:
            logger.error(f"Module not found: {module_id}")
            return False
        
        module = self._modules[module_id]
        module.status = ModuleStatus.DISABLED
        logger.info(f"Disabled module: {module.name}")
        return True
    
    def get_module(self, module_id: str) -> Optional[ModuleInfo]:
        """Get module info"""
        return self._modules.get(module_id)
    
    def list_modules(
        self, 
        tier: Optional[int] = None,
        category: Optional[str] = None,
        status: Optional[ModuleStatus] = None
    ) -> List[ModuleInfo]:
        """List modules with optional filters"""
        modules = list(self._modules.values())
        
        if tier is not None:
            modules = [m for m in modules if m.tier == tier]
        
        if category is not None:
            modules = [m for m in modules if m.category == category]
        
        if status is not None:
            modules = [m for m in modules if m.status == status]
        
        return modules
    
    def get_enabled_modules(self) -> List[ModuleInfo]:
        """Get all enabled modules"""
        return self.list_modules(status=ModuleStatus.ENABLED)
    
    def register_router(self, module_id: str, router: Any) -> None:
        """Register FastAPI router for a module"""
        self._loaded_routers[module_id] = router
        logger.info(f"Registered router for module: {module_id}")
    
    def get_router(self, module_id: str) -> Optional[Any]:
        """Get registered router"""
        return self._loaded_routers.get(module_id)
