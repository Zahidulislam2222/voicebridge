import { Component } from 'react';
import type { ReactNode } from 'react';
import { content } from '../data';
import { Button, Icon } from './ui';

export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <main className="error-screen">
        <Icon name="alert" size={36} />
        <h1>{content.labels.errorTitle}</h1>
        <p>{content.labels.errorBoundary}</p>
        <Button onClick={() => window.location.reload()}>{content.labels.restart}</Button>
      </main>
    ) : (
      this.props.children
    );
  }
}
