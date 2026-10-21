import { ref, watch } from 'vue'

const KUNCI = 'tema'

// bawaan terang, tema gelap hanya kalau pengguna pernah memilihnya
function temaAwal() {
  try {
    if (localStorage.getItem(KUNCI) === 'dark') return 'dark'
  } catch {
    // localStorage bisa diblokir browser, tetap pakai tema terang
  }
  return 'light'
}

const tema = ref(temaAwal())

watch(
  tema,
  (nilai) => {
    document.documentElement.dataset.theme = nilai
  },
  { immediate: true },
)

function gantiTema() {
  tema.value = tema.value === 'dark' ? 'light' : 'dark'
  try {
    localStorage.setItem(KUNCI, tema.value)
  } catch {
    // tidak tersimpan, tema tetap berganti untuk sesi ini
  }
}

export function useTheme() {
  return { tema, gantiTema }
}
