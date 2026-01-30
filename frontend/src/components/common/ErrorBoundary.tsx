import React, { Component, ErrorInfo, ReactNode } from 'react';

interface FallbackProps {
  error: Error;
  reset: () => void;
}

interface Props {
  children?: ReactNode;
  fallback?: ReactNode | ((props: FallbackProps) => ReactNode);
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  private reset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  public render() {
    if (this.state.hasError) {
      if (typeof this.props.fallback === 'function') {
        return this.props.fallback({
          error: this.state.error || new Error('Unknown error'),
          reset: this.reset
        });
      }

      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center h-full w-full p-4 bg-gray-900 text-white rounded-lg border border-red-500/30">
          <div className="text-red-400 text-3xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold mb-2 text-red-300">Something went wrong</h2>
          <p className="text-gray-400 mb-4 text-center max-w-md text-sm">
            {this.state.error?.message || "An unexpected error occurred."}
          </p>
          <button
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors text-sm"
            onClick={this.reset}
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
