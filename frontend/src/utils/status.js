export const STATUS_BOOKING = {
  menunggu_pembayaran: { label: 'Menunggu pembayaran', nada: 'warning' },
  menunggu_persetujuan: { label: 'Menunggu persetujuan', nada: 'info' },
  terkonfirmasi: { label: 'Terkonfirmasi', nada: 'success' },
  selesai: { label: 'Selesai', nada: '' },
  dibatalkan: { label: 'Dibatalkan', nada: 'danger' },
  ditolak: { label: 'Ditolak', nada: 'danger' },
  kedaluwarsa: { label: 'Kedaluwarsa', nada: 'muted' },
}

export const METODE_BAYAR = {
  qris: 'QRIS',
  transfer: 'Transfer bank',
  ewallet: 'E-wallet',
}

export const JENIS_BAYAR = {
  deposit: 'Deposit (DP)',
  pelunasan: 'Pelunasan',
  refund: 'Refund',
}

export const MODE_KONFIRMASI = {
  otomatis: 'Otomatis setelah DP dibayar',
  manual: 'Disetujui manager',
}

export const STATUS_SLOT = {
  tersedia: 'Tersedia',
  menunggu: 'Ditahan',
  dipesan: 'Penuh',
  milik_saya: 'Booking kamu',
  ditutup: 'Tutup',
  lewat: 'Lewat',
}
