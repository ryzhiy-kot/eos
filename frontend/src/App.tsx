import { useAuthStore } from './store/authStore';
import AppShell from './components/layout/AppShell';
import LoginForm from './components/auth/LoginForm';

function App() {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

    return (
        isAuthenticated ? <AppShell /> : <LoginForm />
    );
}

export default App;
