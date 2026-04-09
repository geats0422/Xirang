from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.integrations.agents.client import AgentsClient


LEARNING_PATH_GENERATION_PROMPT = """You are a learning path designer for an educational gamified learning platform.

Knowledge points from the study material:
{knowledge_points}

Learning modes:
- speed: Speed Survival mode - fast-paced true/false questions
- draft: Knowledge Draft mode - multiple choice questions
- endless: Endless Abyss mode - fill-in-the-blank questions

Task:
Design a linear learning path with stages for the "{mode}" mode.

Requirements:
1. A learning path has N stages (typically 3-5) arranged linearly
2. Each stage should cover a subset of knowledge points
3. Stages should progress from easier to harder concepts
4. Each stage needs:
   - A unique stage_id (like "R1", "R2", "R3" for routes or "F1", "F2", "F3" for floors)
   - A descriptive label
   - A list of knowledge points covered in that stage

Output format:
Return a JSON object with a "stages" array, where each stage is:
{{
  "stage_id": "R1",
  "label": "Stage 1: Introduction",
  "knowledge_points": ["Point A", "Point B", "Point C"]
}}

Important:
- Generate between 3-5 stages
- First stage should cover foundational/easiest concepts
- Last stage should cover advanced/hardest concepts
- Return ONLY valid JSON with a "stages" array"""


async def generate_learning_path_stages(
    llm_client: AgentsClient,
    knowledge_points: list[str],
    mode: str,
) -> list[dict[str, object]]:
    prompt = LEARNING_PATH_GENERATION_PROMPT.format(
        knowledge_points="\n".join(f"- {kp}" for kp in knowledge_points),
        mode=mode,
    )

    response = await llm_client.generate(
        prompt=prompt,
        response_format={"type": "json_object"},
    )

    data = response.get("structured_output", response.get("content", "{}"))
    parsed: dict[str, object] = json.loads(data) if isinstance(data, str) else data

    stages_data = parsed.get("stages")
    if not isinstance(stages_data, list):
        return []
    return stages_data
