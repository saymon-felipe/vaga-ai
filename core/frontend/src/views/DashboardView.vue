<script setup>
import { ref, computed } from 'vue'

const timeFilter = ref('24h')

const appliedJobsData = {
  '24h': { total: 12, subtitle: 'Últimas 24 horas', trend: '+2 hoje', trendColor: 'text-emerald-400' },
  '1w': { total: 45, subtitle: 'Últimos 7 dias', trend: '+15 esta semana', trendColor: 'text-emerald-400' },
  '1m': { total: 142, subtitle: 'Últimos 30 dias', trend: '+42 este mês', trendColor: 'text-indigo-400' }
}
const currentApplied = computed(() => appliedJobsData[timeFilter.value])

const profileMatch = ref(85)
const marketStacks = ref([
  { name: 'Python', salary: 'R$ 12.000', percentage: 90 },
  { name: 'Docker', salary: 'R$ 11.500', percentage: 80 },
  { name: 'Vue.js', salary: 'R$ 9.500', percentage: 65 },
  { name: 'MongoDB', salary: 'R$ 9.000', percentage: 60 },
  { name: 'OpenAI API', salary: 'R$ 14.000', percentage: 40 },
])
</script>

<template>
  <div class="space-y-6">
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      
      <div class="group relative bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-6 overflow-hidden transition-all duration-500 hover:bg-white/10 hover:shadow-[0_0_40px_-10px_rgba(99,102,241,0.3)] hover:-translate-y-1">
        <div class="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
        
        <div class="relative z-10">
          <div class="flex justify-between items-start mb-6">
            <div>
              <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-1">Vagas Aplicadas</h3>
              <p class="text-5xl font-black text-white tracking-tight">{{ currentApplied.total }}</p>
            </div>
            <div class="relative">
              <select v-model="timeFilter" class="appearance-none bg-slate-800/50 border border-white/10 text-slate-300 text-xs font-medium rounded-xl px-4 py-2 pr-8 outline-none focus:ring-2 focus:ring-indigo-500/50 cursor-pointer backdrop-blur-sm transition-all">
                <option value="24h">24 Horas</option>
                <option value="1w">1 Semana</option>
                <option value="1m">1 Mês</option>
              </select>
              <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg class="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
              </div>
            </div>
          </div>
          <div class="flex items-center text-sm">
            <span class="font-bold px-2.5 py-1 rounded-lg bg-white/5 border border-white/5" :class="currentApplied.trendColor">
              {{ currentApplied.trend }}
            </span>
            <span class="text-slate-500 ml-3 text-xs font-medium uppercase tracking-wider">vs período anterior</span>
          </div>
        </div>
      </div>

      <div class="group relative bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-6 overflow-hidden transition-all duration-500 hover:bg-white/10 hover:shadow-[0_0_40px_-10px_rgba(168,85,247,0.3)] hover:-translate-y-1">
        <div class="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
        
        <div class="relative z-10 flex flex-col h-full justify-between">
          <div>
            <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-1">Adequação do Perfil</h3>
            <div class="flex items-baseline gap-2">
              <p class="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight">{{ profileMatch }}%</p>
              <p class="text-slate-500 text-sm font-medium">Match Score</p>
            </div>
          </div>
          
          <div class="mt-6">
            <div class="w-full bg-slate-800/50 rounded-full h-3 p-0.5 border border-white/5 shadow-inner">
              <div 
                class="bg-gradient-to-r from-indigo-500 to-purple-500 h-full rounded-full shadow-[0_0_15px_rgba(99,102,241,0.5)] transition-all duration-1000 ease-out relative" 
                :style="{ width: profileMatch + '%' }"
              >
                <div class="absolute right-0 top-0 bottom-0 w-4 bg-white/30 rounded-full blur-[2px]"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <div class="bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-8 transition-all duration-500 hover:bg-white/[0.07]">
      <h3 class="text-sm font-semibold text-slate-300 uppercase tracking-widest mb-8 flex items-center gap-3">
        <span class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
        Top Stacks do Mercado & Remuneração
      </h3>
      
      <div class="space-y-6">
        <div v-for="(stack, index) in marketStacks" :key="stack.name" class="group relative">
          <div class="flex justify-between items-end mb-2">
            <span class="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">{{ stack.name }}</span>
            <span class="text-xs font-bold font-mono text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded border border-emerald-400/20">{{ stack.salary }}</span>
          </div>
          <div class="w-full bg-slate-800/50 rounded-full h-2 overflow-hidden border border-white/5">
            <div 
              class="h-full rounded-r-full transition-all duration-1000 ease-out relative"
              :class="index % 2 === 0 ? 'bg-gradient-to-r from-indigo-500 to-indigo-400' : 'bg-gradient-to-r from-purple-500 to-purple-400'"
              :style="{ width: stack.percentage + '%' }"
            ></div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>