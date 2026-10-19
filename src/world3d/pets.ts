// The six fantasy pets: three growth forms each, with the name of the power each form can release.
// The look (Blender models, clips Idle and Cast) is in public/models/pet_<id>_<stage>.glb; the effects are in fxRecipes.ts.
import type { Vec3 } from './fx';

export interface PetAnchors { mouth: Vec3; top: Vec3; body: Vec3 } // model space: +Y up, +Z forward, feet at 0
export interface PetStageInfo {
  name_th: string;
  power_th: string;
  power_en: string;
  anchors: PetAnchors;
  /** size factor for effects */
  k: number;
}
export interface PetDef {
  id: string;
  gender: 'male' | 'female';
  tagline_th: string;
  accent: string;
  forms: [PetStageInfo, PetStageInfo, PetStageInfo];
}

const A = (mouth: Vec3, top: Vec3, body: Vec3): PetAnchors => ({ mouth, top, body });

export const PETS: Record<string, PetDef> = {
  skyra: {
    id: 'skyra', gender: 'male', tagline_th: 'สายฟ้าแห่งท้องฟ้า', accent: '#3d84df',
    forms: [
      { name_th: 'หยกน้อย', power_th: 'โจมตีพายุสายฟ้า', power_en: 'Storm Strike', anchors: A([0, 0.79, 0.54], [0, 1.4, 0], [0, 0.45, 0]), k: 1 },
      { name_th: 'อินทรีหนุ่ม', power_th: 'กรงเล็บฟ้าผ่า', power_en: 'Thunder Claw', anchors: A([0, 1.26, 0.99], [0, 2.0, -0.3], [0, 0.85, 0]), k: 1.2 },
      { name_th: 'อินทรีเทพ', power_th: 'ปีกแห่งสายลม', power_en: 'Wings of the Wind', anchors: A([0, 1.64, 1.29], [0, 2.7, -0.4], [0, 1.1, 0]), k: 1.55 },
    ],
  },
  blazion: {
    id: 'blazion', gender: 'male', tagline_th: 'เปลวไฟแห่งความกล้า', accent: '#e0502e',
    forms: [
      { name_th: 'มังกรน้อย', power_th: 'เปลวเพลิงพุ่ง', power_en: 'Flame Breath', anchors: A([0, 0.78, 0.77], [0, 1.4, 0], [0, 0.45, 0]), k: 1 },
      { name_th: 'มังกรวัยรุ่น', power_th: 'ระเบิดไฟ', power_en: 'Fire Blast', anchors: A([0, 1.31, 1.14], [0, 2.1, -0.3], [0, 0.75, 0]), k: 1.2 },
      { name_th: 'มังกรเทพ', power_th: 'วงล้อมังกรเพลิง', power_en: 'Dragon Fire Wheel', anchors: A([0, 1.6, 1.39], [0, 2.5, -0.4], [0, 0.9, 0]), k: 1.55 },
    ],
  },
  kirin: {
    id: 'kirin', gender: 'male', tagline_th: 'จิตวิญญาณแห่งป่า', accent: '#2fa56a',
    forms: [
      { name_th: 'ลูกคีริน', power_th: 'พลังรากไม้', power_en: 'Root Power', anchors: A([0, 0.75, 0.7], [0, 1.5, -0.1], [0, 0.45, 0]), k: 1 },
      { name_th: 'คีรินหนุ่ม', power_th: 'ใบไม้พิษ', power_en: 'Poison Leaf', anchors: A([0, 1.18, 1.0], [0, 2.2, -0.2], [0, 0.75, 0]), k: 1.2 },
      { name_th: 'คีรินเทพ', power_th: 'พายุแห่งป่า', power_en: 'Forest Storm', anchors: A([0, 1.46, 1.25], [0, 2.9, -0.2], [0, 0.95, 0]), k: 1.55 },
    ],
  },
  lunara: {
    id: 'lunara', gender: 'female', tagline_th: 'แสงจันทร์แห่งความหวัง', accent: '#a58be0',
    forms: [
      { name_th: 'ลูกจันทรา', power_th: 'แสงจันทร์รักษา', power_en: 'Healing Moonlight', anchors: A([0, 0.75, 0.6], [0, 1.5, 0], [0, 0.45, 0]), k: 1 },
      { name_th: 'นางฟ้าวัยรุ่น', power_th: 'วงแหวนจันทรา', power_en: 'Moon Ring', anchors: A([0, 1.2, 0.82], [0, 2.0, -0.1], [0, 0.8, 0]), k: 1.2 },
      { name_th: 'นางฟ้าจันทรา', power_th: 'ปีกแห่งแสงจันทร์', power_en: 'Moonlight Wings', anchors: A([0, 1.5, 1.02], [0, 2.5, -0.1], [0, 1.0, 0]), k: 1.55 },
    ],
  },
  aquaria: {
    id: 'aquaria', gender: 'female', tagline_th: 'สายธารแห่งชีวิต', accent: '#3bb8e8',
    forms: [
      { name_th: 'ลูกน้อย', power_th: 'คลื่นน้ำวน', power_en: 'Whirlpool', anchors: A([0, 0.74, 0.69], [0, 1.4, 0], [0, 0.42, 0]), k: 1 },
      { name_th: 'นางเงือกมังกร', power_th: 'กระแสน้ำศักดิ์สิทธิ์', power_en: 'Holy Stream', anchors: A([0, 1.2, 0.93], [0, 1.85, -0.1], [0, 0.7, 0]), k: 1.2 },
      { name_th: 'ราชินีแห่งท้องทะเล', power_th: 'อัญมณีแห่งท้องทะเล', power_en: 'Sea Gem', anchors: A([0, 1.5, 1.16], [0, 2.4, -0.1], [0, 0.9, 0]), k: 1.55 },
    ],
  },
  kitsune: {
    id: 'kitsune', gender: 'female', tagline_th: 'จิตวิญญาณแห่งความรู้', accent: '#f06a9c',
    forms: [
      { name_th: 'ลูกจิ้งจอก', power_th: 'ลูกไฟแห่งปัญญา', power_en: 'Wisdom Fire', anchors: A([0, 0.7, 0.65], [0, 1.5, 0], [0, 0.4, 0]), k: 1 },
      { name_th: 'จิ้งจอกสาว', power_th: 'หมอกมายา', power_en: 'Illusion Mist', anchors: A([0, 1.2, 0.86], [0, 2.0, -0.1], [0, 0.8, 0]), k: 1.2 },
      { name_th: 'จิ้งจอกเทพ', power_th: 'ประตูแห่งความรู้', power_en: 'Gate of Knowledge', anchors: A([0, 1.5, 1.07], [0, 2.5, -0.1], [0, 1.0, 0]), k: 1.55 },
    ],
  },
};

export const PET_IDS = Object.keys(PETS);
export const isFantasyPet = (id: string | undefined | null): id is string => !!id && id in PETS;
export const clampStage = (stage: number): 1 | 2 | 3 => (stage >= 3 ? 3 : stage <= 1 ? 1 : 2);
export const petModelName = (id: string, stage: number) => `pet_${id}_${clampStage(stage)}`;
export const petForm = (id: string, stage: number): PetStageInfo => PETS[id].forms[clampStage(stage) - 1];
