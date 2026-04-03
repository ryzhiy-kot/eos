<script lang="ts">
  import Header from "$lib/components/layout/Header.svelte";
  import { checkAuth } from "$lib/stores/auth";
  import { onMount } from "svelte";

  let { children } = $props();

  onMount(() => {
    checkAuth();
  });
</script>

<div class="app-shell">
  <Header />
  <main class="main-content">
    {@render children()}
  </main>
</div>

<style>
  .app-shell {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
  }

  .main-content {
    flex: 1;
    overflow: auto;
    padding: 12px;
    background: var(--bg-primary);
  }
</style>
