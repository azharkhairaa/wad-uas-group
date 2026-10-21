// pilihan slot = rentang jam berurutan {mulai, durasi} di satu court

export function berisi(pilihan, jam) {
  return !!pilihan && jam >= pilihan.mulai && jam < pilihan.mulai + pilihan.durasi
}

export function semuaTersedia(slots, mulai, durasi) {
  for (let j = mulai; j < mulai + durasi; j++) {
    if (slots.find((s) => s.jam === j)?.status !== 'tersedia') return false
  }
  return true
}

/**
 * klik pertama memilih satu jam, klik jam lain memperluas rentang sampai jam itu
 * selama semua jam di antaranya tersedia dan tidak melebihi batas durasi.
 * klik jam ujung rentang memperpendek, klik jam satu-satunya membatalkan pilihan,
 * klik jam di tengah rentang memulai pilihan baru dari jam itu
 */
export function klikSlot(pilihan, jam, slots, maks = 4) {
  if (!pilihan) return { mulai: jam, durasi: 1 }
  const akhir = pilihan.mulai + pilihan.durasi - 1

  if (pilihan.durasi === 1 && jam === pilihan.mulai) return null
  if (jam === pilihan.mulai) return { mulai: jam + 1, durasi: pilihan.durasi - 1 }
  if (jam === akhir) return { mulai: pilihan.mulai, durasi: pilihan.durasi - 1 }
  if (berisi(pilihan, jam)) return { mulai: jam, durasi: 1 }

  const mulai = Math.min(pilihan.mulai, jam)
  const selesai = Math.max(akhir, jam)
  const durasi = selesai - mulai + 1
  if (durasi <= maks && semuaTersedia(slots, mulai, durasi)) return { mulai, durasi }
  return { mulai: jam, durasi: 1 }
}
