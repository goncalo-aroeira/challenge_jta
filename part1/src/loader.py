# part1_geo/src/geo_loader.py

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Location:
    id: int
    name: str
    admin_level: int
    parent_id: Optional[int]
    ancestors_ids: List[int]
    ancestors_names: List[str]
    ancestors_levels: List[int]


@dataclass
class GeoIndex:
    locations: Dict[int, Location]              # id -> Location
    by_city: Dict[str, List[int]]               # "valadares" -> [loc_ids...]
    by_city_state: Dict[tuple[str, str], List[int]]  # ("valadares","viseu") -> [loc_ids...]


def _normalize_name(name: str) -> str:
    """
    Normaliza nomes para lookup:
    - lower case
    - strip espaços
    (se quiseres depois podes remover acentos aqui)
    """
    if name is None:
        return ""
    return " ".join(name.strip().lower().split())


def build_geo_index(json_path: str) -> GeoIndex:
    """
    Lê o portugal.json e devolve uma estrutura GeoIndex com:
    - lista de Location (achatadas)
    - índices by_city e by_city_state
    """
    with open(json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    locations: Dict[int, Location] = {}
    by_city: Dict[str, List[int]] = {}
    by_city_state: Dict[tuple[str, str], List[int]] = {}

    counter = {"value": 0}  # usar dict para mutabilidade dentro da função interna

    def traverse(node: Dict[str, Any],
                 name: str,
                 parent_id: Optional[int],
                 ancestors: List[Location]) -> Location:
        """
        Percorre recursivamente a árvore e cria Location para cada nó.
        """
        counter["value"] += 1
        loc_id = counter["value"]

        admin_level = node.get("admin_level")
        location = Location(
            id=loc_id,
            name=name,
            admin_level=admin_level,
            parent_id=parent_id,
            ancestors_ids=[a.id for a in ancestors],
            ancestors_names=[a.name for a in ancestors],
            ancestors_levels=[a.admin_level for a in ancestors],
        )
        locations[loc_id] = location

        # Index por cidade (nome do próprio nó)
        city_norm = _normalize_name(name)
        if city_norm:
            by_city.setdefault(city_norm, []).append(loc_id)

            # Index por (cidade, "estado")
            # Aqui uma opção simples: para cada ancestor, indexar (cidade, ancestor_name)
            for anc in ancestors:
                state_norm = _normalize_name(anc.name)
                if state_norm:
                    key = (city_norm, state_norm)
                    by_city_state.setdefault(key, []).append(loc_id)

        # Percorrer filhos
        for child_name, child_node in node.get("children", {}).items():
            traverse(
                node=child_node,
                name=child_name,
                parent_id=loc_id,
                ancestors=ancestors + [location],
            )

        return location

    # A raiz do ficheiro é "Portugal" com admin_level 2 e os children são distritos/regiões
    root_node = {
        "admin_level": raw["admin_level"],
        "children": raw["children"],
    }
    traverse(root_node, "portugal", parent_id=None, ancestors=[])

    return GeoIndex(
        locations=locations,
        by_city=by_city,
        by_city_state=by_city_state,
    )
