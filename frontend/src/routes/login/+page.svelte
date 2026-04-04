<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { login, isLoading, authError, isAuthenticated } from "$lib/stores/auth";

  let username = $state("trader");
  let password = $state("trader123");

  onMount(() => {
    if ($isAuthenticated) {
      goto("/");
    }
  });

  async function handleLogin(e: Event) {
    e.preventDefault();
    try {
      await login(username, password);
      goto("/");
    } catch {
      // error is in store
    }
  }
</script>

<div class="login-page">
  <div class="login-card">
    <div class="login-logo">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
        <rect width="24" height="24" rx="4" fill="#3b82f6" />
        <path d="M7 12L12 7L17 12L12 17Z" fill="white" />
      </svg>
    </div>
    <h1>FinAgent</h1>
    <p class="subtitle">AI-Powered Financial Platform</p>

    <form onsubmit={handleLogin}>
      {#if $authError}
        <div class="error">{$authError}</div>
      {/if}
      <div class="field">
        <label for="username">Username</label>
        <input
          id="username"
          type="text"
          class="input"
          bind:value={username}
          placeholder="Enter username"
          autocomplete="username"
        />
      </div>
      <div class="field">
        <label for="password">Password</label>
        <input
          id="password"
          type="password"
          class="input"
          bind:value={password}
          placeholder="Enter password"
          autocomplete="current-password"
        />
      </div>
      <button type="submit" class="btn btn-primary login-btn" disabled={$isLoading}>
        {$isLoading ? "Signing in..." : "Sign In"}
      </button>
    </form>

    <div class="demo-info">
      <span>Demo: trader / trader123</span>
    </div>
  </div>
</div>

<style>
  .login-page {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    background: var(--bg-primary);
  }

  .login-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: 8px;
    padding: 40px;
    width: 360px;
    text-align: center;
  }

  .login-logo {
    margin: 0 auto 16px;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  h1 {
    margin: 0 0 4px;
    font-size: 22px;
    font-weight: 700;
    color: var(--text-primary);
  }

  .subtitle {
    margin: 0 0 28px;
    font-size: 13px;
    color: var(--text-muted);
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .field {
    text-align: left;
  }

  .checkbox-field {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .checkbox-field label {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-size: 12px;
    color: var(--text-secondary);
  }

  .checkbox-field input {
    width: 16px;
    height: 16px;
  }

  label {
    display: block;
    margin-bottom: 6px;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .input {
    width: 100%;
  }

  .login-btn {
    width: 100%;
    padding: 10px;
    font-size: 13px;
    margin-top: 4px;
  }

  .error {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: var(--red);
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 12px;
  }

  .demo-info {
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid var(--border-primary);
    font-size: 11px;
    color: var(--text-muted);
  }
</style>
