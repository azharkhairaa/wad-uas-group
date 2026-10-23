<script setup>
import { reactive, ref } from 'vue'

import { managerApi } from '@/api'
import RequestState from '@/components/RequestState.vue'
import { useRequest } from '@/composables/useRequest'
import { useManagerStore } from '@/stores/manager'
import { useToastStore } from '@/stores/toast'
import { HARI_SENIN, hariIniIso, jam, rentangJam, tanggalPanjang } from '@/utils/format'

const manager = useManagerStore()
const toast = useToastStore()
const JAM = Array.from({ length: 25 }, (_, i) => i)

// jam operasional mingguan
const jadwal = ref(manager.venue.jadwal.map((j) => ({ ...j })))
const menyimpan = ref(false)
const errorJadwal = ref('')

async function simpanJadwal() {
  errorJadwal.value = ''
  const salah = jadwal.value.find((j) => !j.is_tutup && j.jam_buka >= j.jam_tutup)
  if (salah) {
    errorJadwal.value = `Jam tutup hari ${HARI_SENIN[salah.hari]} harus setelah jam buka.`
    return
  }
  menyimpan.value = true
  try {
    // hari tutup tetap dikirim dengan jam valid supaya lolos validasi backend
    const data = jadwal.value.map((j) => ({
      hari: j.hari,
      jam_buka: j.jam_buka,
      jam_tutup: j.jam_tutup > j.jam_buka ? j.jam_tutup : j.jam_buka + 1,
      is_tutup: j.is_tutup,
    }))
    const hasil = await managerApi.ubahJadwal(manager.venue.id, data)
    jadwal.value = hasil.map((j) => ({ ...j }))
    manager.perbarui({ ...manager.venue, jadwal: hasil })
    toast.sukses('Jam operasional disimpan.')
  } catch (e) {
    errorJadwal.value = e.message
  } finally {
    menyimpan.value = false
  }
}

function salinSenin() {
  const senin = jadwal.value[0]
  jadwal.value = jadwal.value.map((j) => ({ ...j, jam_buka: senin.jam_buka, jam_tutup: senin.jam_tutup, is_tutup: senin.is_tutup }))
}

// penutupan sementara
const penutupan = useRequest(managerApi.penutupan)
const muatPenutupan = () => penutupan.jalankan(manager.venue.id)
muatPenutupan()

const form = reactive({
  court_id: manager.venue.courts.find((c) => c.is_active)?.id || null,
  tanggal: hariIniIso(),
  sehari: true,
  jam_mulai: 8,
  jam_selesai: 12,
  alasan: '',
})
const menambah = ref(false)
const menghapusId = ref(null)
const errorTutup = ref('')

async function tambahPenutupan() {
  errorTutup.value = ''
  menambah.value = true
  try {
    await managerApi.tambahPenutupan(manager.venue.id, {
      court_id: form.court_id,
      tanggal: form.tanggal,
      jam_mulai: form.sehari ? null : form.jam_mulai,
      jam_selesai: form.sehari ? null : form.jam_selesai,
      alasan: form.alasan.trim(),
    })
    form.alasan = ''
    toast.sukses('Penutupan ditambahkan. Slot di jam itu tidak bisa dipesan.')
    muatPenutupan()
  } catch (e) {
    errorTutup.value = e.message
  } finally {
    menambah.value = false
  }
}

async function hapusPenutupan(p) {
  menghapusId.value = p.id
  try {
    await managerApi.hapusPenutupan(p.id)
    toast.info(`${p.court.nama} dibuka kembali.`)
    muatPenutupan()
  } catch (e) {
    toast.gagal(e.message)
  } finally {
    menghapusId.value = null
  }
}
</script>

<template>
  <div class="stack">
    <div class="page-head">
      <div>
        <h1>Jam buka & penutupan</h1>
        <p>{{ manager.venue.nama }} · jadwal rutin mingguan dan penutupan sementara per lapang</p>
      </div>
    </div>

    <section class="card card-body">
      <div class="judul">
        <div>
          <h2 class="card-title">Jam operasional mingguan</h2>
          <p class="card-sub">Berlaku untuk semua lapang. Slot booking dibuat per jam di antara jam buka dan tutup.</p>
        </div>
        <button class="btn btn-ghost btn-sm" type="button" @click="salinSenin">Samakan dengan Senin</button>
      </div>
      <div v-if="errorJadwal" class="alert danger" role="alert">{{ errorJadwal }}</div>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>Hari</th><th>Buka</th><th>Tutup</th><th>Libur</th></tr>
          </thead>
          <tbody>
            <tr v-for="j in jadwal" :key="j.hari">
              <td><strong>{{ HARI_SENIN[j.hari] }}</strong></td>
              <td>
                <select v-model.number="j.jam_buka" class="select kecil" :disabled="j.is_tutup" :aria-label="`Jam buka ${HARI_SENIN[j.hari]}`">
                  <option v-for="h in JAM.slice(0, 24)" :key="h" :value="h">{{ jam(h) }}</option>
                </select>
              </td>
              <td>
                <select v-model.number="j.jam_tutup" class="select kecil" :disabled="j.is_tutup" :aria-label="`Jam tutup ${HARI_SENIN[j.hari]}`">
                  <option v-for="h in JAM.slice(1)" :key="h" :value="h">{{ h === 24 ? '24:00' : jam(h) }}</option>
                </select>
              </td>
              <td>
                <label class="check">
                  <input v-model="j.is_tutup" type="checkbox" />
                  Tutup
                </label>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="kaki">
        <p class="muted small">Perubahan ditolak kalau ada booking aktif yang jatuh di luar jam baru.</p>
        <button class="btn btn-primary" :disabled="menyimpan" @click="simpanJadwal">
          <span v-if="menyimpan" class="spinner" aria-hidden="true" />
          {{ menyimpan ? 'Menyimpan...' : 'Simpan jam operasional' }}
        </button>
      </div>
    </section>

    <section class="card card-body">
      <h2 class="card-title">Penutupan sementara</h2>
      <p class="card-sub">Untuk maintenance, turnamen atau acara. Slot yang ditutup tidak bisa dipesan.</p>

      <form class="tutup-form" @submit.prevent="tambahPenutupan">
        <div v-if="errorTutup" class="alert danger full" role="alert">{{ errorTutup }}</div>
        <label class="field">
          <span>Lapang</span>
          <select v-model="form.court_id" class="select" required>
            <option v-for="c in manager.venue.courts" :key="c.id" :value="c.id">{{ c.nama }}</option>
          </select>
        </label>
        <label class="field">
          <span>Tanggal</span>
          <input v-model="form.tanggal" class="input" type="date" :min="hariIniIso()" required />
        </label>
        <label class="check sehari">
          <input v-model="form.sehari" type="checkbox" />
          Sehari penuh
        </label>
        <template v-if="!form.sehari">
          <label class="field">
            <span>Dari jam</span>
            <select v-model.number="form.jam_mulai" class="select">
              <option v-for="h in JAM.slice(0, 24)" :key="h" :value="h">{{ jam(h) }}</option>
            </select>
          </label>
          <label class="field">
            <span>Sampai jam</span>
            <select v-model.number="form.jam_selesai" class="select">
              <option v-for="h in JAM.slice(1)" :key="h" :value="h">{{ jam(h) }}</option>
            </select>
          </label>
        </template>
        <label class="field alasan">
          <span>Alasan</span>
          <input v-model="form.alasan" class="input" minlength="3" maxlength="160" required placeholder="Mis. ganti karpet" />
        </label>
        <button class="btn btn-primary" :disabled="menambah || form.alasan.trim().length < 3">
          <span v-if="menambah" class="spinner" aria-hidden="true" />
          {{ menambah ? 'Menutup lapang...' : 'Tutup lapang' }}
        </button>
      </form>

      <RequestState
        :loading="penutupan.loading.value && !penutupan.data.value"
        :error="penutupan.error.value"
        :kosong="penutupan.kosong.value"
        judul-kosong="Tidak ada penutupan terjadwal"
        :baris="2"
        :tinggi="90"
        @ulang="muatPenutupan"
      >
        <ul class="daftar">
          <li v-for="p in penutupan.data.value" :key="p.id">
            <div>
              <strong>{{ p.court.nama }}</strong>
              <span class="muted small">
                {{ tanggalPanjang(p.tanggal) }} ·
                {{ p.jam_mulai === null ? 'sehari penuh' : rentangJam(p.jam_mulai, p.jam_selesai) }}
                · {{ p.alasan }}
              </span>
            </div>
            <button class="btn btn-ghost btn-sm" :disabled="menghapusId === p.id" @click="hapusPenutupan(p)">
              <span v-if="menghapusId === p.id" class="spinner" aria-hidden="true" />
              {{ menghapusId === p.id ? 'Membuka...' : 'Buka lagi' }}
            </button>
          </li>
        </ul>
      </RequestState>
    </section>
  </div>
</template>

<style scoped>
.page-head {
  margin-bottom: 0;
}

.judul {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.kecil {
  width: auto;
  min-width: 100px;
  min-height: 36px;
  padding: 6px 10px;
}

.kaki {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
}

.tutup-form {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px;
  margin: 16px 0;
  padding: 14px;
  border-radius: var(--radius);
  background: var(--surface-2);
}

.tutup-form .field {
  min-width: 140px;
}

.tutup-form .alasan {
  flex: 1;
  min-width: 200px;
}

.tutup-form .full {
  width: 100%;
}

.sehari {
  min-height: 42px;
}

.daftar li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}

.daftar li:last-child {
  border-bottom: 0;
}

.daftar li > div {
  display: flex;
  flex-direction: column;
}
</style>
