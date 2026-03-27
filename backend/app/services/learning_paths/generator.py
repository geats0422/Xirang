from __future__ import annotations

from app.db.models.learning_paths import LearningPathNodeType


class LearningPathGenerator:
    def build_nodes(self, *, mode: str, version_no: int) -> list[dict[str, object]]:
        mode = mode.lower()
        root_key = f"{mode}-tree-v{version_no}"
        seeds: list[dict[str, object]] = [
            {
                "node_type": LearningPathNodeType.SKILL_TREE,
                "node_key": root_key,
                "parent_key": None,
                "title": f"{mode.title()} Path v{version_no}",
                "description": "Auto-generated learning path",
                "sort_order": 0,
                "is_mode_branch": False,
                "unlock_rule_json": {},
                "question_selector_json": {},
                "meta_json": {"mode": mode, "version_no": version_no},
            }
        ]

        if mode == "endless":
            seeds.extend(self._build_endless_units(root_key))
        elif mode == "speed":
            seeds.extend(self._build_speed_units(root_key))
        else:
            seeds.extend(self._build_draft_units(root_key))
        return seeds

    def _build_endless_units(self, root_key: str) -> list[dict[str, object]]:
        seeds: list[dict[str, object]] = []
        unit_key = "endless-unit-core"
        seeds.append(
            {
                "node_type": LearningPathNodeType.UNIT,
                "node_key": unit_key,
                "parent_key": root_key,
                "title": "Abyss Core",
                "description": "Foundational endless progression",
                "sort_order": 1,
                "is_mode_branch": True,
                "unlock_rule_json": {},
                "question_selector_json": {},
                "meta_json": {},
            }
        )
        for index in range(1, 7):
            floor_key = f"F{index}"
            seeds.append(
                {
                    "node_type": LearningPathNodeType.LEVEL,
                    "node_key": floor_key,
                    "parent_key": unit_key,
                    "title": f"Floor {index}",
                    "description": "Endless floor challenge",
                    "sort_order": 100 + index,
                    "is_mode_branch": True,
                    "unlock_rule_json": {"type": "linear", "after": f"F{index - 1}" if index > 1 else None},
                    "question_selector_json": {"difficulty_hint": index},
                    "meta_json": {"label": floor_key, "kind": "floor", "goal_total": 10},
                }
            )
        return seeds

    def _build_speed_units(self, root_key: str) -> list[dict[str, object]]:
        unit_key = "speed-unit-core"
        routes = [
            ("speed-route-focus", "R1", "Focus route", 8),
            ("speed-route-burst", "R2", "Burst route", 8),
            ("speed-route-endurance", "R3", "Endurance route", 8),
        ]
        seeds: list[dict[str, object]] = [
            {
                "node_type": LearningPathNodeType.UNIT,
                "node_key": unit_key,
                "parent_key": root_key,
                "title": "Speed Core",
                "description": "High-tempo route set",
                "sort_order": 1,
                "is_mode_branch": True,
                "unlock_rule_json": {},
                "question_selector_json": {},
                "meta_json": {},
            }
        ]
        for idx, (key, label, desc, goal_total) in enumerate(routes, start=1):
            seeds.append(
                {
                    "node_type": LearningPathNodeType.LEVEL,
                    "node_key": key,
                    "parent_key": unit_key,
                    "title": label,
                    "description": desc,
                    "sort_order": 100 + idx,
                    "is_mode_branch": True,
                    "unlock_rule_json": {"type": "linear"},
                    "question_selector_json": {"tempo": key},
                    "meta_json": {"label": label, "kind": "checkpoint", "goal_total": goal_total},
                }
            )
        return seeds

    def _build_draft_units(self, root_key: str) -> list[dict[str, object]]:
        unit_key = "draft-unit-core"
        routes = [
            ("draft-route-classic", "R1", "Classic draft", 10),
            ("draft-route-theory", "R2", "Theory route", 10),
            ("draft-route-memory", "R3", "Memory route", 10),
        ]
        seeds: list[dict[str, object]] = [
            {
                "node_type": LearningPathNodeType.UNIT,
                "node_key": unit_key,
                "parent_key": root_key,
                "title": "Draft Core",
                "description": "Knowledge drafting routes",
                "sort_order": 1,
                "is_mode_branch": True,
                "unlock_rule_json": {},
                "question_selector_json": {},
                "meta_json": {},
            }
        ]
        for idx, (key, label, desc, goal_total) in enumerate(routes, start=1):
            seeds.append(
                {
                    "node_type": LearningPathNodeType.LEVEL,
                    "node_key": key,
                    "parent_key": unit_key,
                    "title": label,
                    "description": desc,
                    "sort_order": 100 + idx,
                    "is_mode_branch": True,
                    "unlock_rule_json": {"type": "linear"},
                    "question_selector_json": {"route": key},
                    "meta_json": {"label": label, "kind": "round", "goal_total": goal_total},
                }
            )
        return seeds
