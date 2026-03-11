<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '../services/api'

// Estados de Monitoramento
const stats = ref({ total: 0, recomendadas: 0, aplicadas: 0, ignoradas: 0 })
const ultimasVagas = ref([])
const sistemaPronto = ref(false)
const robotRodando = ref(false)
const carregando = ref(true)
let pollingInterval = null

// Controle do Modal
const vagaSelecionada = ref(null)
const isModalOpen = ref(false)

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
    const res = await api.get('/jobs/status')
    
    const jobs = res.data.jobs || []
    ultimasVagas.value = jobs
    robotRodando.value = res.data.isRunning
    
    stats.value = {
      total: jobs.length,
      recomendadas: jobs.filter(j => j.status === 'Recomendada').length,
      aplicadas: jobs.filter(j => j.status === 'Aplicado').length,
      ignoradas: jobs.filter(j => j.status === 'Ignorado').length
    }
  } catch (e) {
    console.error("Erro ao buscar vagas", e)
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

const abrirModal = (vaga) => {
  // Transforma o texto do banco de volta em Array para listar os tópicos perfeitamente
  let argumentos = []
  try {
    argumentos = typeof vaga.argumentos_match_raw === 'string' 
      ? JSON.parse(vaga.argumentos_match_raw) 
      : vaga.argumentos_match_raw
  } catch (e) {
    argumentos = [vaga.argumentos_match_raw]
  }

  vagaSelecionada.value = { ...vaga, argumentosParsed: argumentos }
  isModalOpen.value = true
  document.body.style.overflow = 'hidden' // Impede rolagem da página de fundo
}

const fecharModal = () => {
  isModalOpen.value = false
  setTimeout(() => { vagaSelecionada.value = null }, 300)
  document.body.style.overflow = 'auto'
}

onMounted(async () => {
  await checkStatusSistema()
  await fetchVagas()
  pollingInterval = setInterval(fetchVagas, 3000)
  carregando.value = false
})

onUnmounted(() => {
  if (pollingInterval) clearInterval(pollingInterval)
})
</script>

<template>
  <div class="space-y-8 relative">
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

    <div class="grid grid-cols-1 gap-8">
      <div class="bg-white/5 border border-white/10 rounded-3xl p-6">
        <h3 class="text-lg font-bold mb-6">Histórico Recente</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-left whitespace-nowrap">
            <thead class="text-slate-500 text-xs uppercase">
              <tr>
                <th class="pb-4 pr-4">Plataforma</th>
                <th class="pb-4 pr-4">Empresa</th>
                <th class="pb-4 pr-4">Vaga</th>
                <th class="pb-4 pr-4">Salário</th>
                <th class="pb-4 pr-4">Match</th>
                <th class="pb-4">Status</th>
              </tr>
            </thead>
            <tbody class="text-sm">
              <tr v-for="vaga in ultimasVagas" :key="vaga.id" class="border-t border-white/5">
                <td class="py-4 pr-4 text-slate-400">{{ vaga.plataforma }}</td>
                <td class="py-4 pr-4 text-white font-medium">{{ vaga.empresa_nome }}</td>
                <td class="py-4 pr-4 text-slate-400 max-w-xs truncate">
                  <button @click="abrirModal(vaga)" class="text-left hover:text-indigo-400 transition-colors cursor-pointer font-medium truncate w-full">
                    {{ vaga.vaga_titulo }}
                  </button>
                </td>
                <td class="py-4 pr-4 text-emerald-400 font-medium">{{ vaga.faixa_salarial || 'A Combinar' }}</td>
                <td class="py-4 pr-4">
                  <span :class="vaga.match_score >= 85 ? 'text-green-400' : 'text-cyan-400'" class="font-bold">
                    {{ vaga.match_score }}%
                  </span>
                </td>
                <td class="py-4">
                  <span :class="[
                    vaga.status === 'Aplicado' ? 'bg-green-500/20 text-green-400' : 
                    vaga.status === 'Recomendada' ? 'bg-indigo-500/20 text-indigo-400' : 
                    'bg-slate-500/20 text-slate-400'
                  ]" class="px-3 py-1 rounded-full text-[10px] font-bold">
                    {{ vaga.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="fecharModal"></div>
      
      <div class="relative w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col bg-[#0f111a] border border-white/10 rounded-3xl shadow-2xl">
        <div class="p-6 border-b border-white/10 flex justify-between items-start bg-white/5">
          <div>
            <h3 class="text-2xl font-bold text-white">{{ vagaSelecionada?.vaga_titulo }}</h3>
            <div class="flex gap-3 mt-2 text-sm font-medium">
              <span class="text-indigo-400">{{ vagaSelecionada?.empresa_nome }}</span>
              <span class="text-slate-600">•</span>
              <span class="text-slate-400">{{ vagaSelecionada?.plataforma }}</span>
            </div>
          </div>
          <button @click="fecharModal" class="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-white/10 transition-colors cursor-pointer">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-8">
          
          <div class="flex flex-col md:flex-row gap-6 justify-between bg-white/5 p-5 rounded-2xl border border-white/10">
            <div class="flex flex-wrap gap-8">
              <div class="flex flex-col">
                <span class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Score de Alinhamento</span>
                <span class="text-3xl font-black" :class="vagaSelecionada?.match_score >= 85 ? 'text-green-400' : 'text-cyan-400'">
                  {{ vagaSelecionada?.match_score }}%
                </span>
              </div>
              <div class="flex flex-col border-l border-white/10 pl-8">
                <span class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Faixa Salarial Estimada</span>
                <span class="text-2xl font-black text-emerald-400 mt-1">{{ vagaSelecionada?.faixa_salarial || 'A Combinar' }}</span>
              </div>
            </div>
            <a :href="vagaSelecionada?.vaga_url" target="_blank" class="self-center px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-colors shadow-lg shadow-indigo-500/20 whitespace-nowrap text-center">
              Acessar Vaga Original
            </a>
          </div>

          <div>
            <h4 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 border-b border-white/10 pb-2">Por que essa vaga foi selecionada?</h4>
            <ul class="space-y-3">
              <li v-for="(motivo, idx) in vagaSelecionada?.argumentosParsed" :key="idx" class="flex gap-3 text-slate-300 items-start bg-white/5 p-4 rounded-xl">
                <div class="mt-1 text-indigo-400 shrink-0">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                </div>
                <span class="leading-relaxed">{{ motivo }}</span>
              </li>
            </ul>
          </div>

          <div>
            <h4 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 border-b border-white/10 pb-2">Descrição da Vaga</h4>
            <div class="bg-black/20 p-6 rounded-2xl border border-white/5 text-slate-300 text-sm leading-relaxed whitespace-pre-wrap font-sans">
              {{ vagaSelecionada?.job_description_raw }}
            </div>
          </div>
          
        </div>
      </div>
    </div>
    
  </div>
</template>

<style scoped>
/* Estilização da barra de rolagem do modal para combinar com o dark theme */
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>