import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'

import { managerApi } from '@/api'

const KUNCI = 'lapangin.venue'

function idTersimpan() {
  try {
    return Number(localStorage.getItem(KUNCI)) || null
  } catch {
    return null
  }
}

export const useManagerStore = defineStore('manager', () => {
  const venues = ref([])
  const venueId = ref(idTersimpan())
  const loading = ref(false)
  const sudahDimuat = ref(false)
  const error = ref(null)

  const venue = computed(
    () => venues.value.find((v) => v.id === venueId.value) || venues.value[0] || null,
  )

  watch(venueId, (id) => {
    try {
      localStorage.setItem(KUNCI, String(id))
    } catch {
      // pilihan venue tidak tersimpan, tidak masalah
    }
  })

  async function muat() {
    loading.value = true
    error.value = null
    try {
      venues.value = await managerApi.venues()
      if (!venues.value.some((v) => v.id === venueId.value)) {
        venueId.value = venues.value[0]?.id ?? null
      }
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
      sudahDimuat.value = true
    }
  }

  // ganti data satu venue setelah disunting tanpa memuat ulang semuanya
  function perbarui(data) {
    const i = venues.value.findIndex((v) => v.id === data.id)
    if (i === -1) venues.value.push(data)
    else venues.value[i] = data
  }

  function reset() {
    venues.value = []
    sudahDimuat.value = false
  }

  return { venues, venueId, venue, loading, sudahDimuat, error, muat, perbarui, reset }
})
