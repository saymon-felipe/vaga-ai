<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../services/api'

// Estados de Monitoramento
const stats = ref({ total: 0, aplicadas: 0, analisando: 0, erro: 0 })
const vagaAtual = ref(null)
const ultimasVagas = ref([])
const sistemaPronto = ref(false)
const robotRodando = ref(false)
const carregando = ref(true)

// Requisitos para o botão
const requisitos = ref({
  perfil: false,
  skills: false,
  comportamental: false,
  trajetoria: false
})

const checkStatusSistema = async () => {
  try {
    const [p, s, b, t] = await Promise.all([
      api.get('/profile'),
      api.get('/skills'),
      api.get('/behavioral'),
      api.get('/trajectory')
    ])
    
    // Validação simples: verificar se retornaram dados
    requisitos.value.perfil = !!p.data?.nome
    requisitos.value.skills = s.data?.length > 0
    requisitos.value.comportamental = !!b.data?.ai_analysis
    requisitos.value.trajetoria = t.data?.length > 0

    sistemaPronto.value = Object.values(requisitos.value).every(v => v === true)
  } catch (e) {
    console.error("Erro ao validar sistema", e)
  }
}

const fetchVagas = async () => {
  try {
    const res = await api.get('/jobs/status') // Precisaremos criar esta rota no back
    ultimasVagas.value = res.data.recentes
    stats.value = res.data.stats
    vagaAtual.value = res.data.processando
  } catch (e) {
    console.error(e)
  }
}

const toggleRobot = async () => {
  if (!sistemaPronto.value) return
  
  try {
    const endpoint = robotRodando.value ? '/jobs/stop' : '/jobs/start'
    await api.post(endpoint, { cargo: 'Desenvolvedor', localizacao: 'Remoto' })
    robotRodando.value = !robotRodando.value
  } catch (e) {
    alert("Erro ao controlar o robô")
  }
}

onMounted(async () => {
  await checkStatusSistema()
  await fetchVagas()
  // Polling para atualização em tempo real a cada 5 segundos
  setInterval(fetchVagas, 5000)
  carregando.value = false
})
</script>

<template>
  <div class="space-y-8">
    <div class="bg-white/5 border border-white/10 p-8 rounded-3xl backdrop-blur-xl flex flex-col md:flex-row justify-between items-center gap-6">
      <div>
        <h2 class="text-2xl font-bold text-white mb-2">Painel de Operações</h2>
        <p class="text-slate-400 text-sm" v-if="sistemaPronto">Sistema pronto para buscar oportunidades.</p>
        <p class="text-red-400 text-sm font-medium" v-else>Complete seu perfil, skills e teste comportamental para iniciar.</p>
      </div>

      <button 
        @click="toggleRobot"
        :disabled="!sistemaPronto"
        :class="[
          !sistemaPronto ? 'opacity-30 cursor-not-allowed bg-slate-700' : 
          robotRodando ? 'bg-red-500 hover:bg-red-600 shadow-red-500/20' : 'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-500/20'
        ]"
        class="group relative px-10 py-4 rounded-2xl font-black uppercase tracking-widest text-white transition-all shadow-2xl cursor-pointer"
      >
        <div v-if="robotRodando" class="absolute -top-1 -right-1 w-3 h-3 bg-red-400 rounded-full animate-ping"></div>
        {{ robotRodando ? 'Parar Automação' : 'Iniciar Robô' }}
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div v-for="(val, label) in stats" :key="label" class="bg-white/5 border border-white/10 p-6 rounded-2xl">
        <p class="text-xs font-bold text-slate-500 uppercase mb-2">{{ label }}</p>
        <p class="text-3xl font-black text-white">{{ val }}</p>
      </div>
    </div>

    <div v-if="vagaAtual" class="bg-indigo-600/10 border border-indigo-500/30 p-6 rounded-2xl animate-pulse">
      <div class="flex items-center gap-4">
        <div class="w-2 h-2 bg-indigo-400 rounded-full"></div>
        <p class="text-indigo-400 font-bold text-sm uppercase tracking-tighter">Processando Agora:</p>
      </div>
      <h3 class="text-xl font-bold text-white mt-2">{{ vagaAtual.vaga_titulo }} @ {{ vagaAtual.empresa_nome }}</h3>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div class="lg:col-span-2 bg-white/5 border border-white/10 rounded-3xl p-6">
        <h3 class="text-lg font-bold mb-6">Histórico Recente</h3>
        <table class="w-full text-left">
          <thead class="text-slate-500 text-xs uppercase">
            <tr>
              <th class="pb-4">Empresa</th>
              <th class="pb-4">Vaga</th>
              <th class="pb-4">Match</th>
              <th class="pb-4">Status</th>
            </tr>
          </thead>
          <tbody class="text-sm">
            <tr v-for="vaga in ultimasVagas" :key="vaga.id" class="border-t border-white/5">
              <td class="py-4 text-white font-medium">{{ vaga.empresa_nome }}</td>
              <td class="py-4 text-slate-400">{{ vaga.vaga_titulo }}</td>
              <td class="py-4">
                <span class="text-cyan-400 font-bold">{{ vaga.match_score }}%</span>
              </td>
              <td class="py-4">
                <span :class="vaga.status === 'Aplicado' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'" class="px-3 py-1 rounded-full text-[10px] font-bold">
                  {{ vaga.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>