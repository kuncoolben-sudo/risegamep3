// Model URLs respect Vite's base path (GitHub Pages serves under /<repo>/).
export const modelUrl = (name: string) => `${import.meta.env.BASE_URL}models/${name}.glb`;
