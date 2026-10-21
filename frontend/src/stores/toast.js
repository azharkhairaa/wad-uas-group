import { ref } from 'vue'
import { defineStore } from 'pinia'

let nomor = 0

export const useToastStore = defineStore('toast', () => {
  const daftar = ref([])

  function tutup(id) {
    daftar.value = daftar.value.filter((t) => t.id !== id)
  }

  function tampilkan(pesan, jenis = 'success', lama = 4500) {
    const id = ++nomor
    daftar.value.push({ id, pesan, jenis })
    setTimeout(() => tutup(id), lama)
  }

  return {
    daftar,
    tutup,
    sukses: (pesan) => tampilkan(pesan, 'success'),
    gagal: (pesan) => tampilkan(pesan, 'danger', 6500),
    info: (pesan) => tampilkan(pesan, 'info'),
  }
})
