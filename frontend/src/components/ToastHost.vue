<script setup>
import AppIcon from '@/components/AppIcon'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const IKON = { success: 'check', danger: 'alert', info: 'info' }
</script>

<template>
  <TransitionGroup name="toast" tag="div" class="toasts" role="status" aria-live="polite">
    <div v-for="t in toast.daftar" :key="t.id" class="toast" :class="t.jenis">
      <span class="ikon"><AppIcon :name="IKON[t.jenis]" :size="14" :stroke="2.5" /></span>
      <p>{{ t.pesan }}</p>
      <button class="tutup" aria-label="Tutup notifikasi" @click="toast.tutup(t.id)"><AppIcon name="close" :size="16" /></button>
    </div>
  </TransitionGroup>
</template>

<style scoped>
.toasts {
  position: fixed;
  right: 16px;
  bottom: 16px;
  z-index: 200;
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: min(380px, calc(100vw - 32px));
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  box-shadow: 0 12px 32px rgb(0 0 0 / 18%);
  font-size: 0.9rem;
}

.toast p {
  flex: 1;
}

.ikon {
  display: grid;
  place-items: center;
  flex: none;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  font-weight: 800;
  font-size: 0.8rem;
  background: var(--info-soft);
  color: var(--info);
}

.success .ikon {
  background: var(--success-soft);
  color: var(--success);
}

.danger .ikon {
  background: var(--danger-soft);
  color: var(--danger);
}

.tutup {
  border: 0;
  background: none;
  font-size: 1.2rem;
  line-height: 1;
  color: var(--muted);
  cursor: pointer;
}

@keyframes masuk {
  from {
    transform: translateY(8px);
    opacity: 0;
  }
}
</style>
