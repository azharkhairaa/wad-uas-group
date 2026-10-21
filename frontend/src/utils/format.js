const rupiahFmt = new Intl.NumberFormat('id-ID', {
  style: 'currency',
  currency: 'IDR',
  maximumFractionDigits: 0,
})

export const BULAN = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
export const HARI = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu']
// urutan hari versi backend: 0 = Senin
export const HARI_SENIN = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

export function rupiah(nilai) {
  return rupiahFmt.format(nilai ?? 0).replace(/\s/g, '')
}

export function rupiahRingkas(nilai) {
  if (nilai >= 1_000_000) return `${(nilai / 1_000_000).toLocaleString('id-ID', { maximumFractionDigits: 1 })} jt`
  if (nilai >= 1_000) return `${Math.round(nilai / 1_000)} rb`
  return String(nilai)
}

// tanggal "YYYY-MM-DD" dibaca sebagai tanggal lokal, bukan UTC
export function keTanggal(iso) {
  if (iso instanceof Date) return iso
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function isoTanggal(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function hariIniIso() {
  return isoTanggal(new Date())
}

export function geserHari(iso, jumlah) {
  const d = keTanggal(iso)
  d.setDate(d.getDate() + jumlah)
  return isoTanggal(d)
}

export function tanggalPanjang(iso) {
  const d = keTanggal(iso)
  return `${HARI[d.getDay()]}, ${d.getDate()} ${BULAN[d.getMonth()]} ${d.getFullYear()}`
}

export function tanggalSingkat(iso) {
  const d = keTanggal(iso)
  return `${HARI[d.getDay()].slice(0, 3)}, ${d.getDate()} ${BULAN[d.getMonth()]}`
}

export function tanggalPendek(iso) {
  const d = keTanggal(iso)
  return `${d.getDate()} ${BULAN[d.getMonth()]}`
}

export function jam(nilai) {
  return `${String(nilai).padStart(2, '0')}:00`
}

export function rentangJam(mulai, selesai) {
  return `${jam(mulai)}–${jam(selesai)}`
}

export function waktuLengkap(isoDatetime) {
  if (!isoDatetime) return '-'
  const d = new Date(isoDatetime)
  const pukul = d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
  return `${d.getDate()} ${BULAN[d.getMonth()]} ${d.getFullYear()}, ${pukul}`
}

export function pukul(isoDatetime) {
  return new Date(isoDatetime).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
}

export function persen(nilai) {
  return `${Number(nilai).toLocaleString('id-ID', { maximumFractionDigits: 1 })}%`
}
