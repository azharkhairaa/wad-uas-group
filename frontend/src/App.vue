<script setup>
import { RouterView } from 'vue-router'

import AppFooter from '@/components/AppFooter.vue'
import AppHeader from '@/components/AppHeader.vue'
import BottomNav from '@/components/BottomNav.vue'
import LoadingBar from '@/components/LoadingBar.vue'
import ToastHost from '@/components/ToastHost.vue'
import { useTheme } from '@/composables/useTheme'

useTheme()
</script>

<template>
  <div class="app">
    <LoadingBar />
    <a class="skip" href="#konten">Lewati ke konten</a>
    <AppHeader />
    <main id="konten" class="app-main">
      <RouterView v-slot="{ Component, route }">
        <Transition name="page" mode="out-in">
          <component :is="Component" :key="route.matched[0]?.path || route.path" />
        </Transition>
      </RouterView>
    </main>
    <AppFooter />
    <BottomNav />
    <ToastHost />
  </div>
</template>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-main {
  flex: 1;
  min-width: 0;
}

.skip {
  position: absolute;
  left: 12px;
  top: -60px;
  z-index: 100;
  padding: 8px 14px;
  border-radius: 8px;
  background: var(--brand);
  color: var(--on-brand);
}

.skip:focus {
  top: 12px;
}

@media (max-width: 820px) {
  .app-main {
    padding-bottom: 68px;
  }
}
</style>
