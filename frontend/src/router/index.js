import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import History from '../views/History.vue'
import Camera from '../views/Camera.vue'
 
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/',        component: Dashboard },
    { path: '/history', component: History },
    { path: '/camera',  component: Camera },
  ]
})
 
export default router
 