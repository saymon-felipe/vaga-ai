<script setup>
import { ref, computed, markRaw, onMounted } from 'vue'
import api from './services/api' // Importando a instância do axios

import DashboardView from './views/DashboardView.vue'
import ProfileView from './views/ProfileView.vue'
import SkillsView from './views/SkillsView.vue'
import BehavioralView from './views/BehavioralView.vue'
import TrajectoryView from './views/TrajectoryView.vue'

const activeTab = ref('dashboard')
const usuarioFoto = ref(null) // Estado para armazenar a foto do perfil

// Busca a foto do usuário ao carregar a aplicação
const carregarFotoPerfil = async () => {
  try {
    const response = await api.get('/profile')
    if (response.data && response.data.fotoUrl) {
      usuarioFoto.value = response.data.fotoUrl
    }
  } catch (error) {
    console.error("Erro ao carregar avatar no topo:", error)
  }
}

onMounted(() => {
  carregarFotoPerfil()
})

const menuItems = [
  { id: 'dashboard', name: 'Dashboard', icon: 'M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z', component: markRaw(DashboardView) },
  { id: 'perfil', name: 'Meu Perfil', icon: 'M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z', component: markRaw(ProfileView) },
  { id: 'skills', name: 'Skills', icon: 'M21.99 4c0-1.1-.89-2-1.99-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4-.01-18z', component: markRaw(SkillsView) },
  { id: 'comportamental', name: 'Comportamental', icon: 'M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z', component: markRaw(BehavioralView) },
  { id: 'trajetoria', name: 'Trajetória', icon: 'M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z', component: markRaw(TrajectoryView) },
]

const currentComponent = computed(() => {
  const tab = menuItems.find(item => item.id === activeTab.value)
  return tab ? tab.component : menuItems[0].component
})

const currentTitle = computed(() => {
  const tab = menuItems.find(item => item.id === activeTab.value)
  return tab ? tab.name : 'Dashboard'
})
</script>

<template>
  <div class="relative flex h-screen bg-slate-950 text-slate-200 font-sans overflow-hidden selection:bg-indigo-500/30">
    
    <div class="absolute top-[-10%] left-[-10%] w-[40vw] h-[40vw] bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none"></div>
    <div class="absolute bottom-[-10%] right-[-10%] w-[30vw] h-[30vw] bg-purple-600/20 rounded-full blur-[100px] pointer-events-none"></div>

    <aside class="relative z-10 w-24 hover:w-64 group flex flex-col m-4 bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] overflow-hidden">
      
      <div class="flex items-center pl-[1.8rem] group-hover:pl-6 h-20 border-b border-white/5 transition-all duration-300">
        <div class="w-10 h-10 flex-shrink-0 flex items-center justify-center">
          <img src="@/assets/img/vaga-ai.png" alt="Logo" class="w-full h-full object-contain" />
        </div>
        <h1 class="text-xl font-black tracking-tighter transition-all duration-300 whitespace-nowrap overflow-hidden max-w-0 opacity-0 group-hover:max-w-xs group-hover:opacity-100 group-hover:ml-4">
          Vaga<span class="font-black bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-purple-500">AI</span>
        </h1>
      </div>
      
      <nav class="flex-1 py-6 px-3 space-y-3 overflow-y-auto no-scrollbar">
        <button 
          v-for="item in menuItems" 
          :key="item.id"
          @click="activeTab = item.id"
          class="relative flex items-center w-full px-6 py-3 rounded-2xl cursor-pointer transition-all duration-300 group/btn"
          :class="activeTab === item.id ? 'bg-white/10 shadow-lg shadow-black/20 text-white' : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'"
        >
          <div v-if="activeTab === item.id" class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-indigo-400 to-purple-400 rounded-r-full"></div>
          
          <svg class="w-6 h-6 flex-shrink-0 transition-transform duration-300 group-hover/btn:scale-110" :class="activeTab === item.id ? 'fill-indigo-400' : 'fill-current'" viewBox="0 0 24 24">
            <path :d="item.icon" />
          </svg>
          
          <span class="font-medium transition-all duration-300 whitespace-nowrap overflow-hidden max-w-0 opacity-0 group-hover:max-w-xs group-hover:opacity-100 group-hover:ml-4">
            {{ item.name }}
          </span>
        </button>
      </nav>
    </aside>

    <main class="relative z-10 flex-1 p-8 overflow-y-auto no-scrollbar">
      <header class="mb-10 flex justify-between items-center">
        <h2 class="text-4xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400">
          {{ currentTitle }}
        </h2>
        
        <div class="h-10 w-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 p-[2px] cursor-pointer hover:scale-110 transition-transform duration-300 shadow-lg shadow-indigo-500/20 overflow-hidden">
          <div class="w-full h-full bg-slate-900 rounded-full flex items-center justify-center overflow-hidden">
            <img v-if="usuarioFoto" :src="usuarioFoto" alt="User Avatar" class="w-full h-full object-cover" />
            <span v-else class="text-xs font-bold text-slate-200">EU</span>
          </div>
        </div>
      </header>

      <transition name="scale-fade" mode="out-in">
        <component :is="currentComponent" />
      </transition>
    </main>
  </div>
</template>