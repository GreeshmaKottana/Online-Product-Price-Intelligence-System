import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    console.error('Frontend runtime error:', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="app-shell">
          <section className="results-shell">
            <span className="eyebrow">Application Error</span>
            <h2>Something went wrong while rendering the comparison page.</h2>
            <p className="status-message muted">
              Refresh the page and try again. If the issue persists, inspect the browser console.
            </p>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
