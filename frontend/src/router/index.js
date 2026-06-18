import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    component: () => import('../layout/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('../views/Home.vue'),
      },
      {
        path: 'classrooms',
        name: 'Classrooms',
        component: () => import('../views/Classrooms.vue'),
      },
      {
        path: 'classrooms/:id',
        name: 'ClassroomDetail',
        component: () => import('../views/ClassroomDetail.vue'),
        props: true,
      },
      {
        path: 'games',
        name: 'Games',
        component: () => import('../views/Games.vue'),
      },
      {
        path: 'games/:id',
        name: 'GameDetail',
        component: () => import('../views/GameDetail.vue'),
        props: true,
      },
      {
        path: 'games/:id/decision',
        name: 'DecisionSubmit',
        component: () => import('../views/DecisionSubmit.vue'),
        props: true,
      },
      {
        path: 'games/:id/dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        props: true,
      },
      {
        path: 'games/:id/ranking',
        name: 'Ranking',
        component: () => import('../views/Ranking.vue'),
        props: true,
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()

  if (!userStore.isLoggedIn && !to.meta.guest) {
    try {
      await userStore.fetchUser()
    } catch {
      // ignore
    }
  }

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else if (to.meta.guest && userStore.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
