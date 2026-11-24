// Keep ids in sync with server/scenarios.py
export const SCENARIOS = [
  { id: 'cafe', title: 'Au café', jp: 'カフェ', emoji: '☕', desc: 'Commander une boisson au comptoir.' },
  { id: 'hotel', title: "À l'hôtel", jp: 'ホテル', emoji: '🏨', desc: 'Faire le check-in à la réception.' },
  { id: 'konbini', title: 'Au konbini', jp: 'コンビニ', emoji: '🏪', desc: 'Payer ses achats à la caisse.' },
] as const

export const LEVELS = ['N5', 'N4', 'N3'] as const

export type ScenarioId = (typeof SCENARIOS)[number]['id']
export type Level = (typeof LEVELS)[number]
