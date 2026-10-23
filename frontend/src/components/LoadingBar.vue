<script setup>
import { useLoadingStore } from '@/stores/loading'

const loading = useLoadingStore()
</script>

<template>
  <div
    class="loading-bar-wrap"
    :class="{ aktif: loading.isActive, error: loading.isError }"
    aria-hidden="true"
  >
    <div
      class="loading-bar"
      :style="{ width: `${loading.progress}%` }"
    />
  </div>
</template>

<style scoped>
.loading-bar-wrap {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 9999;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.25s ease;
}

.loading-bar-wrap.aktif {
  opacity: 1;
}

.loading-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--orange) 0%, var(--brand) 50%, var(--accent) 100%);
  box-shadow: 0 0 10px var(--accent);
  transition: width 0.2s cubic-bezier(0.1, 0.9, 0.2, 1);
}

.loading-bar-wrap.error .loading-bar {
  background: var(--danger);
  box-shadow: 0 0 10px var(--danger);
}
</style>
