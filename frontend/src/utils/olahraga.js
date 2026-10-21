export const OLAHRAGA = {
  tennis: { label: 'Tennis', panjang: 'Lapang Tennis', unit: 'lapang' },
  padel: { label: 'Padel', panjang: 'Lapang Padel', unit: 'lapang' },
  futsal: { label: 'Futsal', panjang: 'Lapang Futsal', unit: 'lapang' },
  golf_driving: { label: 'Golf Driving', panjang: 'Golf Driving', unit: 'bay' },
  badminton: { label: 'Badminton', panjang: 'Lapang Badminton', unit: 'lapang' },
  voli: { label: 'Voli', panjang: 'Lapang Voli', unit: 'lapang' },
  basket: { label: 'Basket', panjang: 'Lapang Basket', unit: 'lapang' },
}

export const DAFTAR_OLAHRAGA = Object.entries(OLAHRAGA).map(([kode, info]) => ({ kode, ...info }))

export function infoOlahraga(kode) {
  return OLAHRAGA[kode] || { label: kode, panjang: kode, unit: 'lapang' }
}
