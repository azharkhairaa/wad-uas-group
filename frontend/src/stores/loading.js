import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useLoadingStore = defineStore('loading', () => {
  const progress = ref(0)
  const isActive = ref(false)
  const isError = ref(false)
  let timer = null
  let reqCount = 0

  function start() {
    isActive.value = true
    isError.value = false
    progress.value = 15
    clearInterval(timer)
    timer = setInterval(() => {
      if (progress.value < 85) {
        progress.value += Math.max(1, Math.floor((90 - progress.value) * 0.15))
      }
    }, 120)
  }

  function finish() {
    progress.value = 100
    clearInterval(timer)
    setTimeout(() => {
      isActive.value = false
      setTimeout(() => {
        progress.value = 0
        isError.value = false
      }, 200)
    }, 300)
  }

  function fail() {
    isError.value = true
    progress.value = 100
    clearInterval(timer)
    setTimeout(() => {
      isActive.value = false
      setTimeout(() => {
        progress.value = 0
        isError.value = false
      }, 200)
    }, 400)
  }

  function startRequest() {
    reqCount++
    if (reqCount === 1) {
      start()
    }
  }

  function finishRequest(success = true) {
    reqCount = Math.max(0, reqCount - 1)
    if (reqCount === 0) {
      if (success) {
        finish()
      } else {
        fail()
      }
    }
  }

  return {
    progress,
    isActive,
    isError,
    start,
    finish,
    fail,
    startRequest,
    finishRequest,
  }
})
