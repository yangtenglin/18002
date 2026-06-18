import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const isLoggedIn = computed(() => !!user.value)
  const isTeacher = computed(() => user.value?.role === 'teacher')
  const isStudent = computed(() => user.value?.role === 'student')

  async function fetchUser() {
    try {
      const data = await authApi.me()
      user.value = data
    } catch {
      user.value = null
    }
  }

  async function login(formData) {
    const data = await authApi.login(formData)
    user.value = data.user
    return data
  }

  async function register(formData) {
    const data = await authApi.register(formData)
    return data
  }

  async function logout() {
    await authApi.logout()
    user.value = null
  }

  return { user, isLoggedIn, isTeacher, isStudent, fetchUser, login, register, logout }
})
