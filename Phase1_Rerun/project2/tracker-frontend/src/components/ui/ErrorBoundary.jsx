import { Component } from 'react';

class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        // hasError: do we show fallback or children?
        // error: the actual error object (for display/logging)
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        //update state so next render shows fallback UI
        return { hasError: true, error};
    }

    //called after the error is caught - good place to log to a service
    componentDidCatch(error, info) {
        console.error("ErrorBoundary caught an error:", error, info.CompenentStack);
    }

    render() {
        if (this.state.hasError) {
            return(
                <div className='error-fallback'>
                    <h2>Something went wrong</h2>
                    <p>{this.state.error?.message || 'Please try refreshing the page'}</p>
                    <button onClick={() => window.location.reload()}>Reload page</button>
                </div>
            );
        }

        return this.props.children;
    }


}

export default ErrorBoundary;