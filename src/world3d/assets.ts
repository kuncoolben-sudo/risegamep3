import { useGLTF } from '@react-three/drei';

// Model URLs respect Vite's base path (GitHub Pages serves under /<repo>/).
export const modelUrl = (name: string) => `${import.meta.env.BASE_URL}models/${name}.glb`;

// The landmark models are Draco-compressed; decode them with our own copy of three's decoder (public/draco/), not a CDN.
useGLTF.setDecoderPath(`${import.meta.env.BASE_URL}draco/`);
