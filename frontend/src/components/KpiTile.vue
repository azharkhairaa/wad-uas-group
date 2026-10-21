<script setup>
defineProps({
  label: { type: String, required: true },
  nilai: { type: String, required: true },
  ket: { type: String, default: '' },
  hero: { type: Boolean, default: false },
})
</script>

<template>
  <div class="kpi card" :class="{ hero }">
    <span class="label">{{ label }}</span>
    <strong class="nilai">{{ nilai }}</strong>
    <span v-if="ket" class="ket">{{ ket }}</span>
    <slot />
  </div>
</template>

<style scoped>
.kpi {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px 18px;
  min-width: 0;
}

.label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--muted);
}

.nilai {
  overflow-wrap: anywhere;
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.15;
}

.ket {
  font-size: 0.8rem;
  color: var(--muted);
}

.hero {
  background: linear-gradient(140deg, var(--hero), var(--hero-2));
  border-color: transparent;
  color: var(--on-hero);
}

.hero .label,
.hero .ket {
  color: color-mix(in srgb, var(--on-hero) 75%, transparent);
}

.hero .nilai {
  font-size: 3rem;
}
</style>
