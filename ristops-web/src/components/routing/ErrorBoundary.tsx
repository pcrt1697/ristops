import { Component, useEffect, type ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import { useGlobalError } from '../../context/error.hooks.ts';

interface ErrorBoundaryProps {
  children: ReactNode;
  onError: (msg: string) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    this.props.onError(error.message || 'Something went wrong, please try again.');
  }

  render() {
    if (this.state.hasError) return null;
    return this.props.children;
  }
}

export default function ErrorBoundaryWithReset({ children }: { children: ReactNode }) {
  const location = useLocation();
  const { setError } = useGlobalError();

  useEffect(() => {
    setError(null);
  }, [location.pathname, setError]);

  return (
    <ErrorBoundary key={location.pathname} onError={setError}>
      {children}
    </ErrorBoundary>
  );
}
