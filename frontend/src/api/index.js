import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || error.response?.data?.message || '请求失败'
    if (error.response?.status === 401) {
      ElMessage.warning('请先登录')
      router.push('/login')
    } else if (error.response?.status === 403) {
      const detail = error.response?.data?.detail
      if (detail) {
        ElMessage.error(detail)
      }
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  register: (data) => api.post('/auth/register/', data),
  login: (data) => api.post('/auth/login/', data),
  logout: () => api.post('/auth/logout/'),
  me: () => api.get('/auth/me/'),
}

export const userApi = {
  list: (params) => api.get('/users/', { params }),
}

export const classroomApi = {
  list: () => api.get('/classrooms/'),
  create: (data) => api.post('/classrooms/', data),
  get: (id) => api.get(`/classrooms/${id}/`),
  update: (id, data) => api.put(`/classrooms/${id}/`, data),
  delete: (id) => api.delete(`/classrooms/${id}/`),
  teams: (classroomId) => api.get(`/classrooms/${classroomId}/teams/`),
  createTeam: (classroomId, data) => api.post(`/classrooms/${classroomId}/teams/`, data),
  updateTeam: (classroomId, teamId, data) => api.put(`/classrooms/${classroomId}/teams/${teamId}/`, data),
  deleteTeam: (classroomId, teamId) => api.delete(`/classrooms/${classroomId}/teams/${teamId}/`),
  addMembers: (classroomId, teamId, userIds) => api.post(`/classrooms/${classroomId}/teams/${teamId}/add-members/`, { user_ids: userIds }),
  removeMembers: (classroomId, teamId, userIds) => api.post(`/classrooms/${classroomId}/teams/${teamId}/remove-members/`, { user_ids: userIds }),
}

export const gameApi = {
  list: (params) => api.get('/games/', { params }),
  create: (data) => api.post('/games/', data),
  get: (id) => api.get(`/games/${id}/`),
  update: (id, data) => api.put(`/games/${id}/`, data),
  delete: (id) => api.delete(`/games/${id}/`),
  start: (id) => api.post(`/games/${id}/start/`),
  pause: (id) => api.post(`/games/${id}/pause/`),
  advanceRound: (id) => api.post(`/games/${id}/advance-round/`),
  parameters: (gameId) => api.get(`/games/${gameId}/parameters/`),
  updateParameter: (gameId, paramId, data) => api.put(`/games/${gameId}/parameters/${paramId}/`, data),
}

export const decisionApi = {
  list: (gameId, params) => api.get(`/games/${gameId}/decisions/`, { params }),
  submit: (gameId, data) => api.post(`/games/${gameId}/decisions/`, data),
  get: (gameId, decisionId) => api.get(`/games/${gameId}/decisions/${decisionId}/`),
  myDecision: (gameId) => api.get(`/games/${gameId}/my-decision/`),
}

export const dashboardApi = {
  overview: (gameId) => api.get(`/games/${gameId}/dashboard/`),
  ranking: (gameId) => api.get(`/games/${gameId}/ranking/`),
  roundResult: (gameId, round) => api.get(`/games/${gameId}/results/${round}/`),
  teamTrend: (gameId, teamId) => api.get(`/games/${gameId}/trend/${teamId}/`),
}

export default api
