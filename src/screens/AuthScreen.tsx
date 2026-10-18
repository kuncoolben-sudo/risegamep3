import { useState } from 'react';
import { supabase, errorText } from '../lib/supabase';

export function SetupScreen() {
  return (
    <main className="card center">
      <h1>RISE English Adventure</h1>
      <p>ยังไม่ได้เชื่อมต่อ Supabase</p>
      <ol className="steps">
        <li>คัดลอก <code>.env.example</code> เป็น <code>.env</code></li>
        <li>ใส่ <code>VITE_SUPABASE_URL</code> และ <code>VITE_SUPABASE_ANON_KEY</code> จาก Project Settings → API</li>
        <li>รัน migration และ seed (ดู README) แล้วเปิดเกมใหม่</li>
      </ol>
    </main>
  );
}

export function AuthScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  async function run(fn: () => Promise<{ error: { message: string } | null }>) {
    setBusy(true);
    setErr('');
    const { error } = await fn();
    if (error) setErr(errorText(error));
    setBusy(false);
  }

  return (
    <main className="card center auth">
      <div className="logo">🗺️</div>
      <h1>RISE English Adventure</h1>
      <p className="muted">ผจญภัยในโลกภาษาอังกฤษ พร้อมสัตว์เลี้ยงคู่ใจ</p>
      <button className="btn big" disabled={busy} onClick={() => run(() => supabase.auth.signInAnonymously())}>
        ▶ เล่นเลย (ไม่ต้องสมัคร)
      </button>
      <div className="divider">หรือใช้อีเมลเพื่อเล่นต่อบนเครื่องอื่น</div>
      <input type="email" placeholder="อีเมล" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
      <input type="password" placeholder="รหัสผ่าน (อย่างน้อย 6 ตัว)" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
      <div className="row">
        <button className="btn" disabled={busy || !email || !password} onClick={() => run(() => supabase.auth.signInWithPassword({ email, password }))}>เข้าสู่ระบบ</button>
        <button className="btn ghost" disabled={busy || !email || password.length < 6} onClick={() => run(() => supabase.auth.signUp({ email, password }))}>สมัครใหม่</button>
      </div>
      {err && <p className="error">{err}</p>}
    </main>
  );
}
