# server/core/loader.py
from __future__ import annotations
import importlib.util, pathlib, types

class StrategyMeta(dict): pass

class StrategyLoader:
    def __init__(self, base_dir: str) -> None:
        self.base_dir = pathlib.Path(base_dir)
        self.catalog: list[StrategyMeta] = []

    def discover(self) -> list[StrategyMeta]:
        self.catalog.clear()
        if not self.base_dir.exists():
            return self.catalog
        for p in sorted(self.base_dir.glob("*.py")):
            if p.name == "__init__.py":
                continue
            mod = self._import_module(p)
            if hasattr(mod, "create"):
                inst = mod.create()
                self.catalog.append({
                    "id": getattr(inst, "id", p.stem),
                    "name": getattr(inst, "name", p.stem.replace("_"," ").title()),
                    "description": getattr(inst, "description", ""),
                    "settingsSchema": getattr(inst, "settingsSchema", {})
                })
        return self.catalog

    def load(self, id_or_name: str):
        for p in self.base_dir.glob("*.py"):
            if p.stem == id_or_name:
                return self._import_module(p).create()
        raise KeyError(f"strategy not found: {id_or_name}")

    def _import_module(self, path: pathlib.Path) -> types.ModuleType:
        # 🔧 key change: import with package name so relative imports work
        mod_name = f"server.strategies.{path.stem}"
        spec = importlib.util.spec_from_file_location(mod_name, path)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
