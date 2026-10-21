import { computed, ref, shallowRef } from 'vue'

// empat keadaan request: loading, error, kosong, berhasil
export function useRequest(fungsi) {
  const data = shallowRef(null)
  const loading = ref(false)
  const error = ref(null)
  let urutan = 0

  async function jalankan(...args) {
    // hanya hasil request terakhir yang dipakai, respons lama yang telat diabaikan
    const ke = ++urutan
    loading.value = true
    error.value = null
    try {
      const hasil = await fungsi(...args)
      if (ke === urutan) data.value = hasil
      return hasil
    } catch (e) {
      if (ke === urutan) error.value = e
      return undefined
    } finally {
      if (ke === urutan) loading.value = false
    }
  }

  const kosong = computed(() => {
    if (loading.value || error.value || data.value === null) return false
    if (Array.isArray(data.value)) return data.value.length === 0
    if (Array.isArray(data.value?.items)) return data.value.items.length === 0
    return false
  })

  return { data, loading, error, kosong, jalankan }
}
