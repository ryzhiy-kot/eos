<script lang="ts">
  import { onMount } from "svelte";
  import ChatPanel from "$lib/components/agent/ChatPanel.svelte";
  import { isAuthenticated } from "$lib/stores/auth";
  import { goto } from "$app/navigation";

  onMount(() => {
    if (!$isAuthenticated) { goto("/login"); return; }
  });
</script>

<div class="agent-page">
  <ChatPanel />
</div>

<style>
  .agent-page {
    height: calc(100vh - 68px);
    display: flex;
    flex-direction: column;
  }
</style>
