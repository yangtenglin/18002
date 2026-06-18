import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/login',
    name: 'RoleSelect',
    component: () => import('../views/RoleSelect.vue'),
    meta: { guest: true },
  },
  {
    path: '/login/teacher',
    name: 'TeacherLogin',
    component: () => import('../views/TeacherLogin.vue'),
    meta: { guest: true },
  },
  {
    path: '/login/student',
    name: 'StudentLogin',
    component: () => import('../views/StudentLogin.vue'),
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
        meta: { roles: ['teacher'] },
      },
      {
        path: 'classrooms/:id',
        name: 'ClassroomDetail',
        component: () => import('../views/ClassroomDetail.vue'),
        props: true,
        meta: { roles: ['teacher'] },
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
        meta: { roles: ['student'] },
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
    return
  }

  if (to.meta.guest && userStore.isLoggedIn) {
    next(userStore.isTeacher ? '/classrooms' : '/games')
    return
  }

  if (to.meta.roles && userStore.isLoggedIn) {
    const userRole = userStore.user?.role
    if (!to.meta.roles.includes(userRole)) {
      next(userRole === 'teacher' ? '/classrooms' : '/games')
      return
    }
  }

  next()
})

export default router
