<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

import AppIcon from '@/components/AppIcon'

// memakai <dialog> bawaan browser: fokus terkunci di dalam modal dan tombol Esc menutup
const props = defineProps({
  buka: { type: Boolean, default: false },
  judul: { type: String, required: true },
  lebar: { type: Number, default: 520 },
})
const emit = defineEmits(['tutup'])
const dialog = ref(null)

watch(
  () => props.buka,
  (nilai) => {
    if (!dialog.value) return
    if (nilai && !dialog.value.open) dialog.value.showModal()
    if (!nilai && dialog.value.open) dialog.value.close()
  },
  { flush: 'post' },
)

function klikLatar(event) {
  if (event.target === dialog.value) emit('tutup')
}

onMounted(() => props.buka && dialog.value.showModal())
onBeforeUnmount(() => dialog.value?.open && dialog.value.close())
</script>

<template>
  <dialog
    ref="dialog"
    class="modal"
    :style="{ '--lebar': `${lebar}px` }"
    @cancel.prevent="emit('tutup')"
    @click="klikLatar"
  >
    <div v-if="buka" class="isi">
      <header class="kepala">
        <h2>{{ judul }}</h2>
        <button class="btn btn-ghost btn-sm" aria-label="Tutup" @click="emit('tutup')"><AppIcon name="close" :size="18" /></button>
      </header>
      <div class="badan">
        <slot />
      </div>
      <footer v-if="$slots.aksi" class="kaki">
        <slot name="aksi" />
      </footer>
    </div>
  </dialog>
</template>

<style scoped>
.modal {
  width: min(var(--lebar), calc(100vw - 24px));
  max-height: calc(100vh - 48px);
  padding: 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  color: var(--text);
  box-shadow: 0 24px 64px rgb(0 0 0 / 30%);
}

.modal::backdrop {
  background: rgb(8 16 12 / 55%);
}

.kepala {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.kepala h2 {
  font-size: 1.1rem;
}

.badan {
  padding: 20px;
}

.kaki {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  padding: 14px 20px;
  border-top: 1px solid var(--border);
  background: var(--surface-2);
}
</style>
