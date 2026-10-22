<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  slug: { type: String, required: true },
  venueNama: { type: String, default: '' },
})

const GALERI_DATA = {
  'setiabudi-padel-tennis': [
    {
      src: '/images/venues/setiabudi-padel-tennis/padel-panoramic.jpg',
      judul: 'Lapang Padel Panoramic',
      kategori: 'Lapang Padel',
      deskripsi: 'Dinding kaca tempered tebal dengan rumput sintetis biru standar WPT untuk pantulan bola optimal.',
    },
    {
      src: '/images/venues/setiabudi-padel-tennis/tennis-court.jpg',
      judul: 'Lapang Tennis Clay & Hard Court',
      kategori: 'Lapang Tennis',
      deskripsi: 'Pilihan hard court akrilik dan clay court outdoor dengan pencahayaan LED terang untuk main malam.',
    },
    {
      src: '/images/venues/setiabudi-padel-tennis/kafe-lounge.jpg',
      judul: 'Kafe & Lounge Pemain',
      kategori: 'Fasilitas Venue',
      deskripsi: 'Tempat bersantai nyaman dengan kopi, minuman hidrasi segar, dan area santai setelah tanding.',
    },
    {
      src: '/images/venues/setiabudi-padel-tennis/ruang-ganti.jpg',
      judul: 'Ruang Ganti, Loker & Shower',
      kategori: 'Fasilitas Mandi',
      deskripsi: 'Shower air hangat bersih, loker penyimpanan barang aman, dan ruang ganti terpisah pria/wanita.',
    },
  ],
  'dago-sport-hub': [
    {
      src: '/images/venues/dago-sport-hub/futsal-indoor.jpg',
      judul: 'Lapang Futsal Vinyl & Sintetis',
      kategori: 'Lapang Futsal',
      deskripsi: 'Dua lapang futsal indoor dengan lantai interlock vinyl empuk dan jaring pengaman keliling.',
    },
    {
      src: '/images/venues/dago-sport-hub/badminton-court.jpg',
      judul: 'Lapang Badminton Karpet BWF',
      kategori: 'Lapang Badminton',
      deskripsi: 'Empat lapang bulutangkis berkarpet standar turnamen dengan pencahayaan ramah mata bebas silau.',
    },
    {
      src: '/images/venues/dago-sport-hub/basket-fullcourt.jpg',
      judul: 'Basket Full Court Lantai Kayu',
      kategori: 'Lapang Basket',
      deskripsi: 'Lantai kayu maple berkualitas tinggi dengan ring pegas hidrolik standar pertandingan.',
    },
    {
      src: '/images/venues/dago-sport-hub/tribun-fasilitas.jpg',
      judul: 'Tribun Penonton, Kantin & Musala',
      kategori: 'Fasilitas Venue',
      deskripsi: 'Tribun bertingkat untuk suporter, kantin makanan/minuman lengkap, dan musala bersih.',
    },
  ],
  'arcamanik-golf-range': [
    {
      src: '/images/venues/arcamanik-golf-range/golf-driving-bay.jpg',
      judul: 'Driving Range Bay Bermatras',
      kategori: 'Golf Driving Range',
      deskripsi: 'Bay beratap bermatras rumput sintetis dengan target jarak presisi dan bola latihan berkualitas.',
    },
    {
      src: '/images/venues/arcamanik-golf-range/golf-simulator.jpg',
      judul: 'Bay Simulator Layar Interaktif',
      kategori: 'Simulator Screen',
      deskripsi: 'Dua bay simulator canggih berlayar lebar dengan analisis ayunan swing untuk segala kondisi cuaca.',
    },
    {
      src: '/images/venues/arcamanik-golf-range/golf-clubhouse.jpg',
      judul: 'Clubhouse, Kafe & Pro Shop',
      kategori: 'Clubhouse & Cafe',
      deskripsi: 'Pemandangan hijau asri, kafe santai, sewa stik golf, dan pelatih golf berpengalaman.',
    },
  ],
  'gor-antapani': [
    {
      src: '/images/venues/gor-antapani/badminton-vinyl.jpg',
      judul: 'Lapang Badminton Karpet Hijau',
      kategori: 'Lapang Badminton',
      deskripsi: 'Gedung olahraga indoor dengan empat lapang badminton sejajar dan ventilasi udara alami yang segar.',
    },
    {
      src: '/images/venues/gor-antapani/futsal-interlock.jpg',
      judul: 'Lapang Futsal Interlock',
      kategori: 'Lapang Futsal',
      deskripsi: 'Lantai interlock awet anti-slip dengan gawang standar dan pencahayaan malam yang terang.',
    },
    {
      src: '/images/venues/gor-antapani/kantin-parkir.jpg',
      judul: 'Kantin Komunitas & Parkir Luas',
      kategori: 'Fasilitas Publik',
      deskripsi: 'Area parkir motor dan mobil luas dengan kantin favorit komunitas olahraga lokal.',
    },
  ],
}

const itemGaleri = computed(() => GALERI_DATA[props.slug] || GALERI_DATA['setiabudi-padel-tennis'])
const indeksAktif = ref(0)
const fotoAktif = computed(() => itemGaleri.value[indeksAktif.value] || itemGaleri.value[0])

let intervalTimer = null

function maju() {
  indeksAktif.value = (indeksAktif.value + 1) % itemGaleri.value.length
}

function mundur() {
  indeksAktif.value = (indeksAktif.value - 1 + itemGaleri.value.length) % itemGaleri.value.length
}

function pilih(idx) {
  indeksAktif.value = idx
  resetAutoPlay()
}

function startAutoPlay() {
  stopAutoPlay()
  intervalTimer = setInterval(() => {
    maju()
  }, 4500)
}

function stopAutoPlay() {
  if (intervalTimer) {
    clearInterval(intervalTimer)
    intervalTimer = null
  }
}

function resetAutoPlay() {
  startAutoPlay()
}

onMounted(() => {
  startAutoPlay()
})

onBeforeUnmount(() => {
  stopAutoPlay()
})
</script>

<template>
  <section
    v-if="itemGaleri.length"
    class="galeri card"
    aria-label="Galeri foto lapang dan fasilitas"
    @mouseenter="stopAutoPlay"
    @mouseleave="startAutoPlay"
  >
    <!-- Frame Foto Utama -->
    <div class="frame-utama">
      <img
        :src="fotoAktif.src"
        :alt="`${fotoAktif.judul} - ${venueNama}`"
        class="foto-utama"
        loading="lazy"
      />

      <!-- Overlay Gradasi & Keterangan -->
      <div class="overlay-gradasi">
        <div class="teks-keterangan">
          <span class="kategori-badge">{{ fotoAktif.kategori }}</span>
          <h3 class="foto-judul">{{ fotoAktif.judul }}</h3>
          <p class="foto-deskripsi">{{ fotoAktif.deskripsi }}</p>
        </div>
      </div>

      <!-- Counter Angka Pojok Kanan Atas -->
      <div class="counter-badge" aria-label="Nomor foto">
        {{ indeksAktif + 1 }} / {{ itemGaleri.length }}
      </div>

      <!-- Tombol Navigasi Kiri & Kanan -->
      <button
        type="button"
        class="nav-panah kiri"
        aria-label="Foto sebelumnya"
        @click.stop="mundur(); resetAutoPlay()"
      >
        &#10094;
      </button>
      <button
        type="button"
        class="nav-panah kanan"
        aria-label="Foto berikutnya"
        @click.stop="maju(); resetAutoPlay()"
      >
        &#10095;
      </button>

      <!-- Dots Indikator -->
      <div class="dots" role="tablist" aria-label="Pilih foto">
        <button
          v-for="(f, idx) in itemGaleri"
          :key="f.src"
          type="button"
          role="tab"
          :aria-selected="idx === indeksAktif"
          :aria-label="`Buka foto ${f.judul}`"
          class="dot"
          :class="{ aktif: idx === indeksAktif }"
          @click.stop="pilih(idx)"
        />
      </div>
    </div>

    <!-- Strip Thumbnail di Bawah Foto Utama -->
    <div class="thumbnail-strip" role="group" aria-label="Daftar thumbnail">
      <button
        v-for="(f, idx) in itemGaleri"
        :key="f.src"
        type="button"
        class="thumb-btn"
        :class="{ aktif: idx === indeksAktif }"
        :aria-pressed="idx === indeksAktif"
        @click="pilih(idx)"
      >
        <img :src="f.src" :alt="f.judul" class="thumb-img" />
        <span class="thumb-label">{{ f.judul }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.galeri {
  overflow: hidden;
  border-radius: var(--radius);
  background: var(--surface);
  border: 1px solid var(--border);
  margin-bottom: 4px;
}

.frame-utama {
  position: relative;
  width: 100%;
  height: 290px;
  background: var(--surface-2);
  overflow: hidden;
}

.foto-utama {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.35s ease;
}

.frame-utama:hover .foto-utama {
  transform: scale(1.02);
}

.overlay-gradasi {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: flex-end;
  background: linear-gradient(
    180deg,
    transparent 40%,
    rgba(8, 19, 31, 0.45) 70%,
    rgba(8, 19, 31, 0.9) 100%
  );
  padding: 16px 20px;
  pointer-events: none;
}

.teks-keterangan {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 82%;
  color: #ffffff;
}

.kategori-badge {
  align-self: flex-start;
  padding: 3px 9px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-radius: 999px;
  background: var(--accent);
  color: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.foto-judul {
  font-size: 1.15rem;
  font-weight: 800;
  color: #ffffff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
  margin: 0;
}

.foto-deskripsi {
  font-size: 0.82rem;
  line-height: 1.35;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.counter-badge {
  position: absolute;
  top: 14px;
  right: 14px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 700;
  color: #ffffff;
  background: rgba(15, 34, 54, 0.65);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.nav-panah {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.25);
  background: rgba(15, 34, 54, 0.6);
  color: #ffffff;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.15s, transform 0.15s;
  backdrop-filter: blur(4px);
}

.nav-panah:hover {
  background: var(--brand);
  transform: translateY(-50%) scale(1.08);
}

.nav-panah.kiri {
  left: 14px;
}

.nav-panah.kanan {
  right: 14px;
}

.dots {
  position: absolute;
  bottom: 14px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  z-index: 2;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.45);
  padding: 0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.dot.aktif {
  width: 20px;
  border-radius: 999px;
  background: #ffffff;
}

/* Strip Thumbnail */
.thumbnail-strip {
  display: flex;
  gap: 8px;
  padding: 10px 14px;
  overflow-x: auto;
  background: var(--surface-2);
  border-top: 1px solid var(--border);
}

.thumb-btn {
  flex: 1;
  min-width: 110px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--surface);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
}

.thumb-btn:hover {
  border-color: var(--brand);
}

.thumb-btn.aktif {
  border-color: var(--brand);
  background: var(--brand-soft);
  box-shadow: 0 0 0 2px var(--brand);
}

.thumb-img {
  width: 44px;
  height: 34px;
  border-radius: 5px;
  object-fit: cover;
  flex-shrink: 0;
}

.thumb-label {
  font-size: 0.76rem;
  font-weight: 600;
  line-height: 1.25;
  color: var(--text);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.thumb-btn.aktif .thumb-label {
  color: var(--brand-ink);
  font-weight: 700;
}

@media (max-width: 768px) {
  .frame-utama {
    height: 230px;
  }

  .nav-panah {
    width: 32px;
    height: 32px;
    font-size: 0.85rem;
  }

  .nav-panah.kiri {
    left: 8px;
  }

  .nav-panah.kanan {
    right: 8px;
  }

  .teks-keterangan {
    max-width: 90%;
  }

  .foto-judul {
    font-size: 1rem;
  }

  .foto-deskripsi {
    display: none;
  }

  .thumb-btn {
    min-width: 90px;
    padding: 5px;
  }

  .thumb-label {
    display: none;
  }
}
</style>
