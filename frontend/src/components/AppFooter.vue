<template>
  <footer class="footer">
    <div class="container footer-inner">
      <p>
        <strong>Lapangin</strong> · booking lapang tennis, padel, futsal, golf driving, badminton,
        voli dan basket.
      </p>
      <p class="muted">Pembayaran di aplikasi ini simulasi, tidak ada uang sungguhan yang ditarik.</p>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  border-top: 1px solid var(--border);
  background: var(--surface);
  font-size: 0.86rem;
}

.footer-inner {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 8px;
  padding-top: 20px;
  padding-bottom: 20px;
}
</style>
