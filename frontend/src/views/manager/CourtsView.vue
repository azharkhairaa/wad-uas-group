<script setup>
import { reactive, ref } from 'vue'

import { managerApi } from '@/api'
import AppIcon from '@/components/AppIcon'
import ModalDialog from '@/components/ModalDialog.vue'
import RequestState from '@/components/RequestState.vue'
import { useRequest } from '@/composables/useRequest'
import { useManagerStore } from '@/stores/manager'
import { useToastStore } from '@/stores/toast'
import { rupiah } from '@/utils/format'
import { DAFTAR_OLAHRAGA, infoOlahraga } from '@/utils/olahraga'

const manager = useManagerStore()
const toast = useToastStore()
const { data: courts, loading, error, kosong, jalankan } = useRequest(managerApi.courts)
const muat = () => jalankan(manager.venue.id)
muat()

const KOSONG = {
  nama: '',
  olahraga: 'futsal',
  permukaan: '',
  is_indoor: true,
  kapasitas: null,
  tarif_weekday: 100000,
  tarif_weekend: 150000,
  deskripsi: '',
}
const form = reactive({ ...KOSONG })
const editId = ref(null)
const modal = ref(false)
const hapus = ref(null)
const menyimpan = ref(false)
const menghapus = ref(false)
const pesanError = ref('')

function tambah() {
  Object.assign(form, KOSONG)
  editId.value = null
  pesanError.value = ''
  modal.value = true
}

function ubah(c) {
  Object.assign(form, {
    nama: c.nama,
    olahraga: c.olahraga,
    permukaan: c.permukaan,
    is_indoor: c.is_indoor,
    kapasitas: c.kapasitas,
    tarif_weekday: c.tarif_weekday,
    tarif_weekend: c.tarif_weekend,
    deskripsi: c.deskripsi || '',
  })
  editId.value = c.id
  pesanError.value = ''
  modal.value = true
}

async function sinkron() {
  await Promise.all([muat(), manager.muat()])
}

async function simpan() {
  menyimpan.value = true
  pesanError.value = ''
  const data = {
    ...form,
    kapasitas: form.kapasitas || null,
    deskripsi: form.deskripsi.trim() || null,
    tarif_weekday: Number(form.tarif_weekday),
    tarif_weekend: Number(form.tarif_weekend),
  }
  try {
    if (editId.value) {
      await managerApi.ubahCourt(editId.value, data)
      toast.sukses(`${data.nama} diperbarui.`)
    } else {
      await managerApi.tambahCourt(manager.venue.id, data)
      toast.sukses(`${data.nama} ditambahkan.`)
    }
    modal.value = false
    sinkron()
  } catch (e) {
    pesanError.value = e.message
  } finally {
    menyimpan.value = false
  }
}

async function gantiAktif(c) {
  try {
    await managerApi.ubahCourt(c.id, { is_active: !c.is_active })
    toast.info(`${c.nama} ${c.is_active ? 'dinonaktifkan, tidak bisa dipesan lagi' : 'aktif kembali'}.`)
    sinkron()
  } catch (e) {
    toast.gagal(e.message)
  }
}

async function konfirmasiHapus() {
  menghapus.value = true
  try {
    await managerApi.hapusCourt(hapus.value.id)
    toast.sukses(`${hapus.value.nama} dihapus.`)
    sinkron()
  } catch (e) {
    toast.gagal(e.message)
  } finally {
    menghapus.value = false
    hapus.value = null
  }
}
</script>

<template>
  <div class="stack">
    <div class="page-head">
      <div>
        <h1>Lapang & tarif</h1>
        <p>Tarif per jam. Weekday = Senin–Jumat, weekend = Sabtu–Minggu.</p>
      </div>
      <button class="btn btn-primary" @click="tambah">+ Tambah lapang</button>
    </div>

    <RequestState
      :loading="loading && !courts"
      :error="error"
      :kosong="kosong"
      judul-kosong="Belum ada lapang"
      pesan-kosong="Tambahkan lapang supaya venue bisa dipesan."
      @ulang="muat"
    >
      <div class="card table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>Lapang</th>
              <th>Weekday</th>
              <th>Weekend</th>
              <th>Status</th>
              <th><span class="sr-only">Aksi</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in courts" :key="c.id" :class="{ nonaktif: !c.is_active }">
              <td>
                <strong class="nowrap sel-ikon"><AppIcon :name="c.olahraga" :size="16" />{{ c.nama }}</strong>
                <div class="muted small">
                  {{ infoOlahraga(c.olahraga).panjang }} · {{ c.permukaan }} · {{ c.is_indoor ? 'Indoor' : 'Outdoor' }}<template v-if="c.kapasitas"> · {{ c.kapasitas }} orang</template>
                </div>
              </td>
              <td class="num nowrap">{{ rupiah(c.tarif_weekday) }}</td>
              <td class="num nowrap">{{ rupiah(c.tarif_weekend) }}</td>
              <td>
                <span class="badge" :class="c.is_active ? 'success' : 'muted'">{{ c.is_active ? 'Aktif' : 'Nonaktif' }}</span>
              </td>
              <td>
                <div class="row aksi">
                  <button class="btn btn-outline btn-sm" @click="ubah(c)">Ubah</button>
                  <button class="btn btn-ghost btn-sm" @click="gantiAktif(c)">{{ c.is_active ? 'Nonaktifkan' : 'Aktifkan' }}</button>
                  <button class="btn btn-ghost btn-sm hapus" :aria-label="`Hapus ${c.nama}`" @click="hapus = c">Hapus</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </RequestState>

    <ModalDialog :buka="modal" :judul="editId ? 'Ubah lapang' : 'Tambah lapang'" :lebar="600" @tutup="modal = false">
      <form id="form-court" class="form-grid" @submit.prevent="simpan">
        <div v-if="pesanError" class="alert danger full" role="alert">{{ pesanError }}</div>
        <label class="field">
          <span>Nama lapang</span>
          <input v-model.trim="form.nama" class="input" required minlength="2" maxlength="60" placeholder="Mis. Futsal A" />
        </label>
        <label class="field">
          <span>Olahraga</span>
          <select v-model="form.olahraga" class="select">
            <option v-for="o in DAFTAR_OLAHRAGA" :key="o.kode" :value="o.kode">{{ o.panjang }}</option>
          </select>
        </label>
        <label class="field">
          <span>Permukaan</span>
          <input v-model.trim="form.permukaan" class="input" required minlength="2" maxlength="60" placeholder="Mis. Vinyl, rumput sintetis" />
        </label>
        <label class="field">
          <span>Kapasitas pemain (opsional)</span>
          <input v-model.number="form.kapasitas" class="input" type="number" min="1" max="50" />
        </label>
        <label class="field">
          <span>Tarif weekday per jam</span>
          <input v-model.number="form.tarif_weekday" class="input" type="number" min="10000" max="10000000" step="5000" required />
          <small>{{ rupiah(form.tarif_weekday) }}</small>
        </label>
        <label class="field">
          <span>Tarif weekend per jam</span>
          <input v-model.number="form.tarif_weekend" class="input" type="number" min="10000" max="10000000" step="5000" required />
          <small>{{ rupiah(form.tarif_weekend) }}</small>
        </label>
        <label class="check full">
          <input v-model="form.is_indoor" type="checkbox" />
          Indoor (beratap)
        </label>
        <label class="field full">
          <span>Deskripsi (opsional)</span>
          <input v-model="form.deskripsi" class="input" maxlength="255" />
        </label>
      </form>
      <template #aksi>
        <button class="btn btn-ghost" :disabled="menyimpan" @click="modal = false">Batal</button>
        <button class="btn btn-primary" type="submit" form="form-court" :disabled="menyimpan">
          <span v-if="menyimpan" class="spinner" aria-hidden="true" />
          {{ menyimpan ? 'Menyimpan...' : (editId ? 'Simpan perubahan' : 'Tambah lapang') }}
        </button>
      </template>
    </ModalDialog>

    <ModalDialog :buka="!!hapus" judul="Hapus lapang?" @tutup="hapus = null">
      <p v-if="hapus">
        {{ hapus.nama }} akan dihapus permanen. Lapang yang sudah punya riwayat booking tidak bisa
        dihapus, nonaktifkan saja supaya riwayatnya tetap utuh.
      </p>
      <template #aksi>
        <button class="btn btn-ghost" :disabled="menghapus" @click="hapus = null">Batal</button>
        <button class="btn btn-danger" :disabled="menghapus" @click="konfirmasiHapus">
          <span v-if="menghapus" class="spinner" aria-hidden="true" />
          {{ menghapus ? 'Menghapus...' : 'Hapus' }}
        </button>
      </template>
    </ModalDialog>
  </div>
</template>

<style scoped>
.page-head {
  margin-bottom: 0;
}

.nonaktif td {
  opacity: 0.6;
}

.nowrap {
  white-space: nowrap;
}

.sel-ikon {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.aksi {
  flex-wrap: nowrap;
  gap: 4px;
}

.hapus {
  color: var(--danger);
}
</style>
