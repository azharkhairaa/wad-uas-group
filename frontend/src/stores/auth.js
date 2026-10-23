import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const siap = ref(false)
  let memuat = null

  const sudahLogin = computed(() => user.value !== null)
  const isSuperadmin = computed(() => user.value?.role === 'superadmin')
  const isManager = computed(() => user.value?.role === 'manager' || user.value?.role === 'superadmin')
  const isCustomer = computed(() => user.value?.role === 'customer' || user.value?.role === 'superadmin')

  // token ada di cookie httpOnly, jadi status login ditanyakan ke /auth/me
  function muat() {
    memuat ||= authApi
      .me()
      .then((data) => {
        user.value = data
      })
      .catch(() => {
        user.value = null
      })
      .finally(() => {
        siap.value = true
      })
    return memuat
  }

  async function login(email, password) {
    const hasil = await authApi.login({ email, password })
    user.value = hasil.user
    return hasil.user
  }

  async function register(data) {
    await authApi.register(data)
    return login(data.email, data.password)
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      user.value = null
    }
  }

  function sesiHabis() {
    user.value = null
  }

  return {
    user,
    siap,
    sudahLogin,
    isSuperadmin,
    isManager,
    isCustomer,
    muat,
    login,
    register,
    logout,
    sesiHabis,
  }
})
