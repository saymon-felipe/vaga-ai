<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import api from '../services/api'

const stats = ref({ total: 0, salvas: 0, aplicadas: 0, descartadas: 0 })
const ultimasVagas = ref([])
const sistemaPronto = ref(false)
const robotRodando = ref(false)
const carregando = ref(true)

let pollingInterval = null
let statsInterval = null
let ultimoIdConhecido = 0
let resumoJaEnviadoHoje = false

const vagaSelecionada = ref(null)
const isModalOpen = ref(false)
const sortKey = ref('createdAt')
const sortOrder = ref(-1) 

const requisitos = ref({
  perfil: false,
  skills: false,
  comportamental: false,
  trajetoria: false
})

const solicitarPermissaoNotificacao = async () => {
  if (!('Notification' in window)) return;
  if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
    await Notification.requestPermission();
  }
}

const enviarNotificacao = (titulo, corpo) => {
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification(titulo, {
      body: corpo,
      icon: '/pwa-192x192.png',
      vibrate: [200, 100, 200]
    });
  }
}

const verificarNotificacoesDeVagas = (novasVagas) => {
  if (ultimoIdConhecido === 0) {
    if (novasVagas.length > 0) ultimoIdConhecido = Math.max(...novasVagas.map(v => v.id));
    return;
  }

  const vagasIneditas = novasVagas.filter(v => v.id > ultimoIdConhecido);
  if (vagasIneditas.length > 0) {
    const recomendadas = vagasIneditas.filter(v => v.status === 'Recomendada');
    if (recomendadas.length > 0) {
      if (recomendadas.length === 1) {
        enviarNotificacao("🚀 Nova Vaga Recomendada!", `${recomendadas[0].vaga_titulo} na ${recomendadas[0].empresa_nome} (Score: ${recomendadas[0].match_score}%)`);
      } else {
        enviarNotificacao("🚀 Novas Vagas Recomendadas!", `Encontramos ${recomendadas.length} novas vagas com alta afinidade para o seu perfil.`);
      }
    }
    ultimoIdConhecido = Math.max(...novasVagas.map(v => v.id));
  }
}

const verificarAlarmeEstatisticas = () => {
  const agora = new Date();
  const hora = agora.getHours();
  const minuto = agora.getMinutes();

  if (hora === 18 && minuto === 0 && !resumoJaEnviadoHoje) {
    enviarNotificacao(
      "📊 Resumo VagaAI do Dia", 
      `Radar encontrou ${stats.value.total} vagas hoje. ${stats.value.salvas} estão aguardando sua revisão!`
    );
    resumoJaEnviadoHoje = true;
  }
  if (hora === 0 && minuto === 0) {
    resumoJaEnviadoHoje = false;
  }
}

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

const atualizarEstatisticas = (jobs) => {
  stats.value = {
    total: jobs.length,
    // Salvas agora é a sua "To-Do list": Apenas vagas que vieram da IA e ainda não foram aplicadas nem descartadas
    salvas: jobs.filter(j => ['Recomendada', 'Salva'].includes(j.status) && !j.applied && !j.discarded).length,
    aplicadas: jobs.filter(j => j.applied === true).length,
    // Soma descartadas pela IA com as descartadas manualmente por você
    descartadas: jobs.filter(j => j.discarded === true || ['Ignorado', 'Descartada'].includes(j.status)).length
  }
}

const fetchVagas = async () => {
  try {
    const res = await api.get('/jobs/status')
    const jobs = res.data.jobs || []
    
    verificarNotificacoesDeVagas(jobs)
    
    ultimasVagas.value = jobs
    robotRodando.value = res.data.isRunning
    atualizarEstatisticas(jobs)
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

const toggleApplied = async () => {
  if (!vagaSelecionada.value) return
  const newValue = !vagaSelecionada.value.applied 
  try {
    await api.put(`/jobs/${vagaSelecionada.value.id}/applied`, { applied: newValue })
    vagaSelecionada.value.applied = newValue
    
    // Se marcou como aplicada, remove o descarte automaticamente
    if (newValue && vagaSelecionada.value.discarded) {
      await toggleDiscardedInterno(false)
    }
    
    atualizaNoStateLocal()
  } catch (error) {
    console.error("Erro ao atualizar o switch de aplicação", error)
  }
}

const toggleDiscardedInterno = async (forceValue) => {
  if (!vagaSelecionada.value) return
  const newValue = forceValue !== undefined ? forceValue : !vagaSelecionada.value.discarded
  
  try {
    await api.put(`/jobs/${vagaSelecionada.value.id}/discarded`, { discarded: newValue })
    vagaSelecionada.value.discarded = newValue
    
    // Se marcou como descartada, remove o aplicado automaticamente
    if (newValue && vagaSelecionada.value.applied) {
      vagaSelecionada.value.applied = false
      await api.put(`/jobs/${vagaSelecionada.value.id}/applied`, { applied: false })
    }
  } catch (error) {
    console.error("Erro ao atualizar o switch de descarte", error)
  }
}

const toggleDiscarded = async () => {
  await toggleDiscardedInterno()
  atualizaNoStateLocal()
}

const atualizaNoStateLocal = () => {
  const index = ultimasVagas.value.findIndex(v => v.id === vagaSelecionada.value.id)
  if (index !== -1) {
    ultimasVagas.value[index].applied = vagaSelecionada.value.applied
    ultimasVagas.value[index].discarded = vagaSelecionada.value.discarded
  }
  atualizarEstatisticas(ultimasVagas.value)
}

const confirmarEmailNoModal = async (id) => {
  try {
    await api.put(`/jobs/${id}/confirm-email`)
    if(vagaSelecionada.value) {
      vagaSelecionada.value.requer_confirmacao_email = false
    }
    await fetchVagas()
  } catch(e) {
    console.error("Erro ao confirmar e-mail", e)
  }
}

const abrirModal = (vaga) => {
  let argumentos = []
  try {
    let parsed = typeof vaga.argumentos_match_raw === 'string' 
      ? JSON.parse(vaga.argumentos_match_raw) 
      : vaga.argumentos_match_raw

    if (typeof parsed === 'string') {
       try { parsed = JSON.parse(parsed) } catch(e) { parsed = [parsed] }
    }
    argumentos = Array.isArray(parsed) ? parsed : [parsed]
  } catch (e) {
    argumentos = [vaga.argumentos_match_raw]
  }

  let descFormatada = vaga.job_description_raw || ''
  if (typeof descFormatada === 'string') {
    descFormatada = descFormatada.replace(/\\n/g, '\n')
  }

  vagaSelecionada.value = { 
    ...vaga, 
    argumentosParsed: argumentos,
    job_description_raw: descFormatada 
  }
  isModalOpen.value = true
  document.body.style.overflow = 'hidden' 
}

const fecharModal = () => {
  isModalOpen.value = false
  setTimeout(() => { vagaSelecionada.value = null }, 300)
  document.body.style.overflow = 'auto'
}

const sortBy = (key) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 1 ? -1 : 1
  } else {
    sortKey.value = key
    sortOrder.value = -1 
  }
}

const vagasOrdenadas = computed(() => {
  return [...ultimasVagas.value].sort((a, b) => {
    let valA = a[sortKey.value]
    let valB = b[sortKey.value]

    if (typeof valA === 'boolean') valA = valA ? 1 : 0
    if (typeof valB === 'boolean') valB = valB ? 1 : 0
    if (typeof valA === 'string') valA = valA.toLowerCase()
    if (typeof valB === 'string') valB = valB.toLowerCase()

    if (valA < valB) return -1 * sortOrder.value
    if (valA > valB) return 1 * sortOrder.value
    return 0
  })
})

onMounted(async () => {
  await solicitarPermissaoNotificacao()
  await checkStatusSistema()
  await fetchVagas()
  pollingInterval = setInterval(fetchVagas, 5000)
  statsInterval = setInterval(verificarAlarmeEstatisticas, 60000) 
  carregando.value = false
})

onUnmounted(() => {
  if (pollingInterval) clearInterval(pollingInterval)
  if (statsInterval) clearInterval(statsInterval)
})
</script>

<template>
  <div class="space-y-6 md:space-y-8 relative pb-20 md:pb-0">
    <div class="bg-white/5 border border-white/10 p-5 md:p-8 rounded-2xl md:rounded-3xl backdrop-blur-xl flex flex-col md:flex-row justify-between items-center gap-4 md:gap-6 sticky top-4 z-10">
      <div class="text-center md:text-left">
        <h2 class="text-xl md:text-2xl font-bold text-white mb-1">Painel de Operações</h2>
        <p class="text-slate-400 text-xs md:text-sm" v-if="sistemaPronto">Radar autônomo de vagas de TI</p>
        <p class="text-red-400 text-xs md:text-sm font-medium" v-else>Complete seu perfil para iniciar.</p>
      </div>

      <button 
        @click="toggleRobot"
        :disabled="!sistemaPronto"
        :class="[
          !sistemaPronto ? 'opacity-30 cursor-not-allowed bg-slate-700' : 
          robotRodando ? 'bg-red-500 hover:bg-red-600 shadow-red-500/20' : 'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-500/20'
        ]"
        class="w-full md:w-auto group relative px-8 py-3.5 md:py-4 rounded-xl md:rounded-2xl font-black uppercase tracking-widest text-white transition-all shadow-xl cursor-pointer text-sm"
      >
        <div v-if="robotRodando" class="absolute top-0 right-0 w-3 h-3 bg-red-400 rounded-full animate-ping mt-1 mr-1"></div>
        {{ robotRodando ? 'Parar Radar' : 'Iniciar Radar' }}
      </button>
    </div>

    <div class="flex overflow-x-auto md:grid md:grid-cols-4 gap-4 md:gap-6 pb-2 snap-x custom-scrollbar">
      <div v-for="(val, label) in stats" :key="label" class="min-w-[140px] md:min-w-0 bg-white/5 border border-white/10 p-5 rounded-2xl snap-center shrink-0">
        <p class="text-[10px] md:text-xs font-bold text-slate-500 uppercase mb-1 md:mb-2">{{ label }}</p>
        <p class="text-2xl md:text-3xl font-black text-white">{{ val }}</p>
      </div>
    </div>

    <div class="bg-white/5 border border-white/10 rounded-2xl md:rounded-3xl p-4 md:p-6 overflow-hidden">
      <h3 class="text-base md:text-lg font-bold mb-4 md:mb-6">Oportunidades Encontradas</h3>
      <div class="overflow-x-auto custom-scrollbar">
        <table class="w-full text-left whitespace-nowrap min-w-[700px]">
          <thead class="text-slate-500 text-xs uppercase select-none border-b border-white/10">
            <tr>
              <th @click="sortBy('plataforma')" class="pb-3 pr-4 cursor-pointer hover:text-white transition-colors">
                Plataforma <span v-show="sortKey === 'plataforma'">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
              </th>
              <th @click="sortBy('empresa_nome')" class="pb-3 pr-4 cursor-pointer hover:text-white transition-colors">
                Empresa <span v-show="sortKey === 'empresa_nome'">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
              </th>
              <th @click="sortBy('vaga_titulo')" class="pb-3 pr-4 cursor-pointer hover:text-white transition-colors">
                Vaga <span v-show="sortKey === 'vaga_titulo'">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
              </th>
              <th @click="sortBy('match_score')" class="pb-3 pr-4 cursor-pointer hover:text-white transition-colors">
                Match <span v-show="sortKey === 'match_score'">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
              </th>
              <th @click="sortBy('status')" class="pb-3 pr-4 cursor-pointer hover:text-white transition-colors">
                Status IA <span v-show="sortKey === 'status'">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
              </th>
              <th @click="sortBy('applied')" class="pb-3 pr-4 cursor-pointer hover:text-white transition-colors">
                Aplicada? <span v-show="sortKey === 'applied'">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
              </th>
              <th @click="sortBy('discarded')" class="pb-3 cursor-pointer hover:text-white transition-colors">
                Descartada? <span v-show="sortKey === 'discarded'">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
              </th>
            </tr>
          </thead>
          <tbody class="text-sm">
            <tr v-for="vaga in vagasOrdenadas" :key="vaga.id" 
                class="border-b border-white/5 transition-all group"
                :class="vaga.discarded ? 'opacity-40 grayscale hover:opacity-100 hover:grayscale-0' : 'hover:bg-white/5'">
              
              <td class="py-3 md:py-4 pr-4 text-slate-400 text-xs md:text-sm">{{ vaga.plataforma }}</td>
              <td class="py-3 md:py-4 pr-4 text-white font-medium text-xs md:text-sm max-w-[120px] truncate">{{ vaga.empresa_nome }}</td>
              <td class="py-3 md:py-4 pr-4 text-slate-400 max-w-[150px] md:max-w-xs truncate">
                <button @click="abrirModal(vaga)" class="text-left hover:text-indigo-400 transition-colors cursor-pointer font-bold text-xs md:text-sm truncate w-full" :class="{'line-through': vaga.discarded}">
                  {{ vaga.vaga_titulo }}
                </button>
              </td>
              <td class="py-3 md:py-4 pr-4">
                <span :class="vaga.match_score >= 85 ? 'text-green-400' : 'text-indigo-400'" class="font-black">
                  {{ vaga.match_score }}%
                </span>
              </td>
              <td class="py-3 md:py-4 pr-4">
                <span :class="[
                  vaga.status === 'Recomendada' ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/20' : 'bg-slate-500/20 text-slate-400 border border-slate-500/20'
                ]" class="px-2 py-1 md:px-3 md:py-1 rounded-full text-[9px] md:text-[10px] font-bold">
                  {{ vaga.status }}
                </span>
              </td>
              <td class="py-3 md:py-4 pr-4">
                <div v-if="vaga.applied" class="flex items-center gap-1.5 text-green-400 font-bold text-xs">
                  <svg class="w-3 h-3 md:w-4 md:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                  Sim
                </div>
                <div v-else class="text-slate-500 font-medium text-xs">-</div>
              </td>
              <td class="py-3 md:py-4">
                <div v-if="vaga.discarded" class="flex items-center gap-1.5 text-red-400 font-bold text-xs">
                  <svg class="w-3 h-3 md:w-4 md:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                  Sim
                </div>
                <div v-else class="text-slate-500 font-medium text-xs">-</div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="vagasOrdenadas.length === 0" class="text-center py-10 text-slate-500">
          Nenhuma vaga registrada ainda.
        </div>
      </div>
    </div>

    <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="fecharModal"></div>
      
      <div class="relative w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col bg-[#0f111a] border border-white/10 rounded-2xl md:rounded-3xl shadow-2xl">
        <div class="p-4 md:p-6 border-b border-white/10 flex flex-col md:flex-row justify-between items-start md:items-center bg-white/5 gap-4">
          <div class="flex-1 pr-4">
            <h3 class="text-lg md:text-2xl font-bold text-white leading-tight" :class="{'line-through text-slate-500': vagaSelecionada?.discarded}">
              {{ vagaSelecionada?.vaga_titulo }}
            </h3>
            <div class="flex flex-wrap gap-2 mt-2 text-xs md:text-sm font-medium">
              <span class="text-indigo-400">{{ vagaSelecionada?.empresa_nome }}</span>
              <span class="text-slate-600 hidden md:inline">•</span>
              <span class="text-slate-400">{{ vagaSelecionada?.plataforma }}</span>
            </div>
          </div>
          
          <div class="flex flex-row items-center gap-2 md:gap-4 w-full md:w-auto overflow-x-auto pb-2 md:pb-0 custom-scrollbar">
            <div class="flex items-center gap-2 bg-black/30 px-3 py-2 rounded-xl border border-white/10 cursor-pointer shrink-0" @click="toggleApplied">
              <span class="text-[10px] md:text-xs font-bold uppercase tracking-widest transition-colors" :class="vagaSelecionada?.applied ? 'text-green-400' : 'text-slate-500'">
                {{ vagaSelecionada?.applied ? '✓ Aplicada' : 'Aplicar' }}
              </span>
              <button 
                class="relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                :class="vagaSelecionada?.applied ? 'bg-green-500' : 'bg-slate-600'"
              >
                <span class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out" :class="vagaSelecionada?.applied ? 'translate-x-4' : 'translate-x-0'"/>
              </button>
            </div>

            <div class="flex items-center gap-2 bg-black/30 px-3 py-2 rounded-xl border border-white/10 cursor-pointer shrink-0" @click="toggleDiscarded">
              <span class="text-[10px] md:text-xs font-bold uppercase tracking-widest transition-colors" :class="vagaSelecionada?.discarded ? 'text-red-400' : 'text-slate-500'">
                {{ vagaSelecionada?.discarded ? '✗ Descartada' : 'Descartar' }}
              </span>
              <button 
                class="relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                :class="vagaSelecionada?.discarded ? 'bg-red-500' : 'bg-slate-600'"
              >
                <span class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out" :class="vagaSelecionada?.discarded ? 'translate-x-4' : 'translate-x-0'"/>
              </button>
            </div>

            <button @click="fecharModal" class="text-slate-400 hover:text-white p-1 ml-auto md:ml-0 rounded-lg hover:bg-white/10 transition-colors cursor-pointer shrink-0">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 md:h-6 md:w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div class="p-4 md:p-6 overflow-y-auto custom-scrollbar flex-1 space-y-6 md:space-y-8" :class="{'opacity-50 grayscale': vagaSelecionada?.discarded}">
          
          <div v-if="vagaSelecionada?.requer_confirmacao_email" class="bg-amber-500/10 border border-amber-500/30 p-4 md:p-5 rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h4 class="text-amber-400 font-bold flex items-center gap-2 text-base md:text-lg">⚠️ Confirmação Necessária</h4>
              <p class="text-xs md:text-sm text-amber-200 mt-1">Acesse seu e-mail e valide o link para concluir o envio da candidatura.</p>
            </div>
            <button @click="confirmarEmailNoModal(vagaSelecionada.id)" class="w-full md:w-auto px-6 py-3 bg-amber-500 hover:bg-amber-600 text-slate-900 font-bold rounded-xl transition-colors shadow-lg shadow-amber-500/20 whitespace-nowrap text-sm">
              Já validei
            </button>
          </div>

          <div class="flex flex-col md:flex-row gap-4 md:gap-6 justify-between bg-white/5 p-4 md:p-5 rounded-2xl border border-white/10">
            <div class="flex gap-4 md:gap-8 justify-between md:justify-start w-full md:w-auto">
              <div class="flex flex-col">
                <span class="text-[10px] md:text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Score de Alinhamento</span>
                <span class="text-2xl md:text-3xl font-black" :class="vagaSelecionada?.match_score >= 85 ? 'text-green-400' : 'text-indigo-400'">
                  {{ vagaSelecionada?.match_score }}%
                </span>
              </div>
              <div class="flex flex-col border-l border-white/10 pl-4 md:pl-8">
                <span class="text-[10px] md:text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Faixa Salarial</span>
                <span class="text-lg md:text-2xl font-black text-emerald-400 mt-1">{{ vagaSelecionada?.faixa_salarial || 'A Combinar' }}</span>
              </div>
            </div>
            <a :href="vagaSelecionada?.vaga_url" target="_blank" class="w-full md:w-auto self-center px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-colors shadow-lg shadow-indigo-500/20 whitespace-nowrap text-center text-sm">
              Acessar Vaga Original
            </a>
          </div>

          <div>
            <h4 class="text-xs md:text-sm font-bold text-slate-400 uppercase tracking-wider mb-3 md:mb-4 border-b border-white/10 pb-2">Por que essa vaga foi selecionada?</h4>
            <ul class="space-y-2 md:space-y-3">
              <li v-for="(motivo, idx) in vagaSelecionada?.argumentosParsed" :key="idx" class="flex gap-3 text-slate-300 items-start bg-white/5 p-3 md:p-4 rounded-xl text-xs md:text-sm">
                <div class="mt-0.5 md:mt-1 text-indigo-400 shrink-0">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 md:h-5 md:w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                </div>
                <span class="leading-relaxed">{{ motivo }}</span>
              </li>
            </ul>
          </div>

          <div>
            <h4 class="text-xs md:text-sm font-bold text-slate-400 uppercase tracking-wider mb-3 md:mb-4 border-b border-white/10 pb-2">Detalhes da Vaga</h4>
            <div class="bg-black/20 p-4 md:p-6 rounded-xl md:rounded-2xl border border-white/5 text-slate-300 text-xs md:text-sm leading-relaxed whitespace-pre-wrap font-sans">
              {{ vagaSelecionada?.job_description_raw }}
            </div>
          </div>
          
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
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