/**
 * PROJECT: MONAD
 * AUTHOR: Kyrylo Yatsenko
 * YEAR: 2026
 * * COPYRIGHT NOTICE:
 * © 2026 Kyrylo Yatsenko. All rights reserved.
 * 
 * This work represents a proprietary methodology for Human-Machine Interaction (HMI).
 * All source code, logic structures, and User Experience (UX) frameworks
 * contained herein are the sole intellectual property of Kyrylo Yatsenko.
 * 
 * ATTRIBUTION REQUIREMENT:
 * Any use of this program, or any portion thereof (including code snippets and
 * interaction patterns), may not be used, redistributed, or adapted
 * without explicit, visible credit to Kyrylo Yatsenko as the original author.
 */

import { useAuthStore } from './store/authStore';
import AppShell from './components/layout/AppShell';
import LoginForm from './components/auth/LoginForm';
import ErrorBoundary from './components/common/ErrorBoundary';

function App() {
    const { isAuthenticated, isHydrated } = useAuthStore();

    if (!isHydrated) return null;

    return (
        <ErrorBoundary>
            {isAuthenticated ? <AppShell /> : <LoginForm />}
        </ErrorBoundary>
    );
}

export default App;
