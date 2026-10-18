export type LocationKind = 'unit' | 'rest' | 'arena' | 'pending';
export type LocationStatus = 'locked' | 'open' | 'cleared';

export interface LocationRow {
  id: string;
  kind: LocationKind;
  name_en: string;
  name_th: string;
  blurb_th: string | null;
  icon: string;
  page_from: number | null;
  page_to: number | null;
  x: number;
  y: number;
  requires: string[];
  rest_type: 'inn' | 'camp' | null;
  content_status: 'verified' | 'pending';
}

export interface LessonRow {
  id: string;
  location_id: string;
  sort: number;
  kind: 'starter' | 'lesson1' | 'lesson2' | 'chat' | 'clil' | 'project';
  title: string;
  pages: string | null;
  required: boolean;
}

export type ActivityType = 'listen_choose' | 'spell' | 'sentence_order' | 'qa_choose' | 'project';

export interface ActivityRow {
  id: number;
  lesson_id: string;
  sort: number;
  type: ActivityType;
  payload: { say?: string; answer?: string; choices?: string[]; question?: string; title?: string };
}

export interface Appearance {
  skin: string;
  hairLength: 'short' | 'long';
  hairType: 'straight' | 'wavy' | 'curly';
  hairColor: string;
  facial: 'none' | 'moustache' | 'beard';
  outfit: string;
}

export interface CharacterRow {
  id: string;
  name: string;
  appearance: Appearance;
  max_hp: number;
  hp: number;
  max_mana: number;
  mana: number;
  coins: number;
  location_id: string;
  rested_here: boolean;
  pvp_wins: number;
  pvp_losses: number;
}

export interface PetRow {
  character_id: string;
  species_id: string;
  nickname: string | null;
  stage: number;
}

export interface PetSpecies {
  id: string;
  name_en: string;
  name_th: string;
  icon: string;
  skill_name: string;
  blurb_th: string | null;
}

export interface ItemRow {
  id: string;
  name_en: string;
  name_th: string;
  icon: string;
  kind: 'heal' | 'mana';
  heal_hp: number;
  heal_mana: number;
  price: number;
}

export interface ProgressRow {
  lesson_id: string;
  stars: number;
  best_correct: number;
  total: number;
  attempts: number;
  note: string | null;
}

export interface LessonResult {
  passed: boolean;
  stars: number;
  coins_gained: number;
  hp: number;
  mana: number;
  new_unlocks: string[];
  evolved: boolean;
  pet_stage?: number;
  item_drop: string | null;
}

export interface MatchRow {
  id: string;
  status: 'waiting' | 'active' | 'finished';
  p1: string;
  p2: string | null;
  p1_name: string;
  p2_name: string | null;
  p1_pet: string;
  p2_pet: string | null;
  p1_stage: number;
  p2_stage: number;
  p1_hp: number;
  p2_hp: number;
  p1_mana: number;
  p2_mana: number;
  p1_guard: boolean;
  p2_guard: boolean;
  turn: string | null;
  round: number;
  q_prompt: string | null;
  q_say: string | null;
  q_choices: string[] | null;
  winner: string | null;
  log: { round: number; actor: string; action: string; correct: boolean; damage: number }[];
  updated_at: string;
}
