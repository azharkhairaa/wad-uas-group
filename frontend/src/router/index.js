import { createRouter, createWebHistory } from 'vue-router'

import { onSesiBerakhir } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: (to, from, posisi) => posisi || (to.path !== from.path ? { top: 0 } : false),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    {
      path: '/venues/:slug',
      name: 'venue',
      component: () => import('@/views/VenueView.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { tamu: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { tamu: true },
    },
    {
      path: '/bookings',
      name: 'bookings',
      component: () => import('@/views/customer/BookingsView.vue'),
      meta: { auth: true, role: 'customer' },
    },
    {
      path: '/bookings/:kode',
      name: 'booking-detail',
      component: () => import('@/views/customer/BookingDetailView.vue'),
      meta: { auth: true, role: 'customer' },
    },
    {
      path: '/manager',
      component: () => import('@/views/manager/ManagerLayout.vue'),
      meta: { auth: true, role: 'manager' },
      children: [
        {
          path: '',
          name: 'manager-dashboard',
          component: () => import('@/views/manager/DashboardView.vue'),
        },
        {
          path: 'bookings',
          name: 'manager-bookings',
          component: () => import('@/views/manager/BookingsView.vue'),
        },
        {
          path: 'agenda',
          name: 'manager-agenda',
          component: () => import('@/views/manager/AgendaView.vue'),
        },
        {
          path: 'courts',
          name: 'manager-courts',
          component: () => import('@/views/manager/CourtsView.vue'),
        },
        {
          path: 'schedule',
          name: 'manager-schedule',
          component: () => import('@/views/manager/ScheduleView.vue'),
        },
        {
          path: 'venue',
          name: 'manager-venue',
          component: () => import('@/views/manager/VenueSettingsView.vue'),
        },
        {
          path: 'users',
          name: 'manager-users',
          component: () => import('@/views/manager/AdminUsersView.vue'),
          meta: { superadminOnly: true },
        },
      ],
    },
    {
      path: '/forbidden',
      name: 'forbidden',
      component: () => import('@/views/ForbiddenView.vue'),
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

// penjaga rute: cek login dan peran sebelum halaman dibuka
router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.muat()

  if (to.meta.tamu && auth.sudahLogin) {
    return auth.isManager ? { name: 'manager-dashboard' } : { name: 'home' }
  }
  if (to.matched.some((r) => r.meta.auth) && !auth.sudahLogin) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.matched.some((r) => r.meta.superadminOnly) && !auth.isSuperadmin) {
    return { name: 'forbidden' }
  }
  const role = to.matched.find((r) => r.meta.role)?.meta.role
  if (role && auth.user?.role !== role && !auth.isSuperadmin) {
    return { name: 'forbidden' }
  }
  return true
})

// token kedaluwarsa di tengah jalan: kembali ke login tanpa kehilangan halaman tujuan
onSesiBerakhir(() => {
  const auth = useAuthStore()
  if (!auth.sudahLogin) return
  auth.sesiHabis()
  useToastStore().info('Sesi kamu sudah berakhir, silakan login lagi.')
  router.push({ name: 'login', query: { redirect: router.currentRoute.value.fullPath } })
})

export default router
