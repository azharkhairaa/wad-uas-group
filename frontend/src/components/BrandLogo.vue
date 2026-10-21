<template>
  <span class="logo">
    <svg viewBox="0 0 64 64" width="32" height="32" aria-hidden="true">
      <rect width="64" height="64" rx="16" fill="var(--brand)" />
      <rect x="14" y="14" width="36" height="36" rx="3" fill="none" stroke="var(--on-brand)" stroke-width="4" />
      <line x1="32" y1="14" x2="32" y2="50" stroke="var(--on-brand)" stroke-width="4" />
      <circle cx="44" cy="22" r="6" fill="var(--accent)" />
    </svg>
    <span class="nama">Lapang<span>in</span></span>
  </span>
</template>

<style scoped>
.logo {
  display: inline-flex;
  align-items: center;
  gap: 9px;
}

.nama {
  font-weight: 800;
  font-size: 1.2rem;
  letter-spacing: -0.02em;
  color: var(--text);
}

.nama span {
  color: var(--brand);
}
</style>
