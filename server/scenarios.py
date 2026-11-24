"""Role-play scenarios and system-prompt builder."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    id: str
    title_fr: str
    bot_role: str  # who the bot plays, in Japanese
    setting: str  # short description of the scene, in Japanese
    opening_hint: str  # how the bot should open the conversation


SCENARIOS: dict[str, Scenario] = {
    "cafe": Scenario(
        id="cafe",
        title_fr="Au café",
        bot_role="カフェの店員",
        setting="東京の小さなカフェ。お客さんがカウンターで注文します。",
        opening_hint="お客さんを迎えて、注文を聞いてください。",
    ),
    "hotel": Scenario(
        id="hotel",
        title_fr="À l'hôtel",
        bot_role="ホテルのフロント係",
        setting="京都のホテルのフロント。お客さんがチェックインに来ました。",
        opening_hint="お客さんを迎えて、予約の名前を聞いてください。",
    ),
    "konbini": Scenario(
        id="konbini",
        title_fr="Au konbini",
        bot_role="コンビニの店員",
        setting="夜のコンビニのレジ。お客さんが商品を持ってきました。",
        opening_hint="お客さんを迎えて、温めやレジ袋が必要か聞いてください。",
    ),
}

LEVELS: dict[str, str] = {
    "N5": (
        "The learner is JLPT N5 (absolute beginner). Use only very basic vocabulary, "
        "です/ます form, and short simple sentences. Speak slowly and clearly."
    ),
    "N4": (
        "The learner is JLPT N4 (elementary). Use everyday vocabulary, polite form, "
        "simple te-form and basic connectors. Avoid rare kanji words."
    ),
    "N3": (
        "The learner is JLPT N3 (intermediate). Use natural everyday Japanese, "
        "including light keigo typical of shop staff, but keep it clear."
    ),
}

DEFAULT_SCENARIO = "cafe"
DEFAULT_LEVEL = "N5"


def build_system_prompt(scenario_id: str, level: str) -> str:
    scenario = SCENARIOS.get(scenario_id, SCENARIOS[DEFAULT_SCENARIO])
    level_rules = LEVELS.get(level, LEVELS[DEFAULT_LEVEL])
    return f"""You are a Japanese conversation partner in a spoken role-play for a language learner.

Role: you are {scenario.bot_role}. Scene: {scenario.setting}
Stay in character for the whole conversation. The learner plays the customer.

Level: {level_rules}

Output rules (your text is converted to speech):
- Reply in Japanese only, at most two short sentences.
- Plain Japanese text: no romaji, no furigana in brackets, no translations, no markdown, no emojis, no lists.

Correcting mistakes:
- If the learner makes a mistake, never stop the role-play to explain it.
- Instead, recast: naturally repeat their idea back in correct Japanese inside your reply, then continue the scene.
  Example: learner says 「コーヒーをください、ふたつ」 → you say 「コーヒーをふたつですね。ホットとアイス、どちらにしますか。」
- If you did not understand, ask them to repeat politely, in character.

If the learner speaks French or English, gently answer in simple Japanese and keep the scene going."""


def opening_instruction(scenario_id: str) -> str:
    scenario = SCENARIOS.get(scenario_id, SCENARIOS[DEFAULT_SCENARIO])
    return f"Start the role-play now. {scenario.opening_hint} One short sentence."
