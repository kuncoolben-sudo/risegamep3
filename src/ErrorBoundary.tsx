import { Component, type ReactNode } from 'react';

// Without this a render error unmounts the whole tree and the page goes blank.
export class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <main className="card center">
        <h2>เกิดข้อผิดพลาด</h2>
        <pre style={{ whiteSpace: 'pre-wrap', textAlign: 'left', fontSize: 13 }}>{String(this.state.error.stack ?? this.state.error.message).slice(0, 800)}</pre>
        <button className="btn" onClick={() => location.reload()}>โหลดใหม่</button>
      </main>
    );
  }
}
