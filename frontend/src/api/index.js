import { http } from './client'

export const authApi = {
  me: () => http.get('/auth/me'),
  login: (data) => http.post('/auth/login', data),
  register: (data) => http.post('/auth/register', data),
  logout: () => http.post('/auth/logout'),
}

export const venueApi = {
  daftar: (params) => http.get('/venues', params),
  detail: (slug) => http.get(`/venues/${encodeURIComponent(slug)}`),
  ketersediaan: (slug, params) => http.get(`/venues/${encodeURIComponent(slug)}/availability`, params),
  kalender: (slug, params) => http.get(`/venues/${encodeURIComponent(slug)}/calendar`, params),
}

export const bookingApi = {
  buat: (data) => http.post('/bookings', data),
  daftar: (params) => http.get('/bookings', params),
  detail: (kode) => http.get(`/bookings/${encodeURIComponent(kode)}`),
  bayar: (kode, data) => http.post(`/bookings/${encodeURIComponent(kode)}/payments`, data),
  batal: (kode, alasan) => http.post(`/bookings/${encodeURIComponent(kode)}/cancel`, { alasan }),
}

const m = '/manager'

export const managerApi = {
  venues: () => http.get(`${m}/venues`),
  tambahVenue: (data) => http.post(`${m}/venues`, data),
  ubahVenue: (id, data) => http.patch(`${m}/venues/${id}`, data),
  jadwal: (id) => http.get(`${m}/venues/${id}/schedule`),
  ubahJadwal: (id, data) => http.put(`${m}/venues/${id}/schedule`, data),
  courts: (id) => http.get(`${m}/venues/${id}/courts`),
  tambahCourt: (id, data) => http.post(`${m}/venues/${id}/courts`, data),
  ubahCourt: (courtId, data) => http.patch(`${m}/courts/${courtId}`, data),
  hapusCourt: (courtId) => http.delete(`${m}/courts/${courtId}`),
  penutupan: (id, params) => http.get(`${m}/venues/${id}/closures`, params),
  tambahPenutupan: (id, data) => http.post(`${m}/venues/${id}/closures`, data),
  hapusPenutupan: (closureId) => http.delete(`${m}/closures/${closureId}`),
  bookings: (params) => http.get(`${m}/bookings`, params),
  booking: (kode) => http.get(`${m}/bookings/${encodeURIComponent(kode)}`),
  setujui: (kode) => http.post(`${m}/bookings/${encodeURIComponent(kode)}/approve`),
  tolak: (kode, alasan) => http.post(`${m}/bookings/${encodeURIComponent(kode)}/reject`, { alasan }),
  selesai: (kode) => http.post(`${m}/bookings/${encodeURIComponent(kode)}/complete`),
  bayar: (kode, data) => http.post(`${m}/bookings/${encodeURIComponent(kode)}/payments`, data),
  batalkan: (kode, alasan) =>
    http.post(`${m}/bookings/${encodeURIComponent(kode)}/cancel`, { alasan }),
  agenda: (id, params) => http.get(`${m}/venues/${id}/agenda`, params),
  dashboard: (id, params) => http.get(`${m}/venues/${id}/dashboard`, params),
}
