const BASE = '/api/v1'

export class ApiError extends Error {
  constructor(message, status, detail = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

function bacaCookie(nama) {
  const baris = document.cookie.split('; ').find((c) => c.startsWith(`${nama}=`))
  return baris ? decodeURIComponent(baris.slice(nama.length + 1)) : ''
}

// ubah detail error FastAPI menjadi satu kalimat yang bisa ditampilkan
function pesanError(detail, status) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    const pertama = detail[0]
    const kolom = pertama.loc?.filter((x) => x !== 'body').join('.')
    const pesan = String(pertama.msg || '').replace(/^Value error, /, '')
    return kolom ? `${kolom}: ${pesan}` : pesan
  }
  if (status === 429) return 'Terlalu banyak percobaan. Tunggu sebentar lalu coba lagi.'
  if (status >= 500) return 'Server sedang bermasalah. Coba lagi beberapa saat lagi.'
  return `Permintaan gagal (${status})`
}

import { useLoadingStore } from '@/stores/loading'

let saatSesiBerakhir = null

export function onSesiBerakhir(fungsi) {
  saatSesiBerakhir = fungsi
}

export async function request(path, { method = 'GET', body, params } = {}) {
  let loadingStore = null
  try {
    loadingStore = useLoadingStore()
    loadingStore.startRequest()
  } catch {
    // pinia belum siap atau konteks non-vue
  }

  const url = new URL(BASE + path, window.location.origin)
  for (const [kunci, nilai] of Object.entries(params || {})) {
    if (nilai !== undefined && nilai !== null && nilai !== '') url.searchParams.set(kunci, nilai)
  }

  const headers = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  // double submit cookie: nilai cookie csrf_token dikirim ulang lewat header
  if (method !== 'GET') headers['X-CSRF-Token'] = bacaCookie('csrf_token')

  let response
  try {
    response = await fetch(url, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: 'same-origin',
    })
  } catch {
    loadingStore?.finishRequest(false)
    throw new ApiError('Tidak bisa terhubung ke server. Cek koneksi lalu coba lagi.', 0)
  }

  const teks = await response.text()
  let data = null
  try {
    data = teks ? JSON.parse(teks) : null
  } catch {
    data = null
  }

  // cek response.ok dulu, jangan anggap request selalu berhasil
  if (!response.ok) {
    loadingStore?.finishRequest(false)
    if (response.status === 401 && saatSesiBerakhir) saatSesiBerakhir()
    throw new ApiError(pesanError(data?.detail, response.status), response.status, data?.detail)
  }
  loadingStore?.finishRequest(true)
  return data
}

export const http = {
  get: (path, params) => request(path, { params }),
  post: (path, body = {}) => request(path, { method: 'POST', body }),
  put: (path, body) => request(path, { method: 'PUT', body }),
  patch: (path, body) => request(path, { method: 'PATCH', body }),
  delete: (path) => request(path, { method: 'DELETE' }),
}
