import { useAuthStore } from './store/authStore';
import AppShell from './components/layout/AppShell';
import LoginForm from './components/auth/LoginForm';

function App() {
    const { isAuthenticated, isHydrated } = useAuthStore();

    if (!isHydrated) return null;

    return (
        isAuthenticated ? <AppShell /> : <LoginForm />
    );
}

export default App;
