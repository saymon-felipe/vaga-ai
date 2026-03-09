<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../services/api'
import VueApexCharts from 'vue3-apexcharts'

const apexchart = VueApexCharts
const loading = ref(true)
const analyzing = ref(false)
const profile = ref(null)
const step = ref(0) // 0: Intro, 1: Quiz, 2: Dashboard

// Perguntas Objetivas Estratégicas
const questions = [
  { id: 1, text: "Em uma reunião de equipe, você geralmente:", options: ["Lidera a discussão e propõe ideias", "Ouve todos antes de opinar", "Foca em dados e fatos técnicos", "Garante que todos se sintam confortáveis"] },
  { id: 2, text: "Como você lida com mudanças inesperadas no projeto?", options: ["Vejo como oportunidade de inovar", "Analiso os riscos metodicamente", "Sigo as novas instruções sem questionar", "Preocupo-me com o impacto na equipe"] },
  { id: 3, text: "Seu ambiente de trabalho ideal é:", options: ["Dinâmico e cheio de desafios", "Organizado e com processos claros", "Colaborativo e amigável", "Autônomo e silencioso"] },
  { id: 4, text: "Ao receber um feedback crítico, sua reação é:", options: ["Argumentar meu ponto de vista", "Refletir e planejar melhorias", "Aceitar para evitar conflitos", "Pedir exemplos práticos e dados"] },
  { id: 5, text: "Qual sua maior força ao resolver problemas?", options: ["Rapidez na tomada de decisão", "Atenção minuciosa aos detalhes", "Criatividade e visão fora da caixa", "Capacidade de mediar opiniões"] }
]

const answers = ref({})
const currentQuestionIndex = ref(0)

const fetchProfile = async () => {
  loading.value = true
  try {
    const response = await api.get('/behavioral')
    
    if (response.data && response.data.ai_analysis) {
      let data = response.data.ai_analysis
      
      if (typeof data === 'string') {
        try {
          data = JSON.parse(data)
        } catch (e) {
          console.error("Erro ao converter ai_analysis para objeto", e)
        }
      }
      
      profile.value = data
      step.value = 2
    }
  } catch (e) { 
    console.error(e) 
  } finally {
    loading.value = false
  }
}

const startQuiz = () => { step.value = 1 }

const nextQuestion = (option) => {
  answers.value[`q${questions[currentQuestionIndex.value].id}`] = option
  if (currentQuestionIndex.value < questions.length - 1) {
    currentQuestionIndex.value++
  } else {
    sendToAnalysis()
  }
}

const sendToAnalysis = async () => {
  analyzing.value = true
  try {
    const response = await api.post('/behavioral/analyze', { answers: answers.value })
    profile.value = response.data.ai_analysis
    step.value = 2
  } catch (e) { console.error(e) }
  analyzing.value = false
}

const resetTest = async () => {
  if (confirm("Deseja refazer o teste? Os dados atuais serão apagados.")) {
    await api.delete('/behavioral')
    profile.value = null
    step.value = 0
    currentQuestionIndex.value = 0
    answers.value = {}
  }
}

// Configuração do Gráfico Radar (DISC)
const chartOptions = computed(() => ({
  chart: { toolbar: { show: false }, dropShadow: { enabled: true, blur: 8, left: 1, top: 1, opacity: 0.2 } },
  colors: ['#6366f1'],
  xaxis: { categories: ['Dominância', 'Influência', 'Estabilidade', 'Conformidade'], labels: { style: { colors: '#94a3b8' } } },
  yaxis: { show: false, max: 100 },
  stroke: { width: 3, curve: 'smooth' },
  fill: { opacity: 0.4 },
  markers: { size: 4 }
}))

const chartSeries = computed(() => {
  if (!profile.value || !profile.value.disc) {
    return [{ name: 'Score', data: [0, 0, 0, 0] }]
  }

  return [{
    name: 'Score',
    data: [
      profile.value.disc.dominancia || 0,
      profile.value.disc.influencia || 0,
      profile.value.disc.estabilidade || 0,
      profile.value.disc.conformidade || 0
    ]
  }]
})

onMounted(fetchProfile)
</script>

<template>
  <div class="max-w-6xl mx-auto p-4 min-h-[70vh] flex flex-col justify-center">

    <div v-if="loading || analyzing" class="text-center space-y-4">
      <div class="inline-block w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin">
      </div>
      <p class="text-slate-400 animate-pulse">{{ analyzing ? 'IA analisando seu perfil...' : 'Carregando...' }}</p>
    </div>

    <div v-else-if="step === 0" class="text-center space-y-8 animate-fade-in">
      <div
        class="w-24 h-24 bg-indigo-500/20 rounded-3xl flex items-center justify-center mx-auto border border-indigo-500/30 shadow-2xl shadow-indigo-500/20">
        <svg class="w-12 h-12 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z">
          </path>
        </svg>
      </div>
      <div class="max-w-xl mx-auto space-y-4">
        <h1 class="text-4xl font-black text-white">Análise Comportamental</h1>
        <p class="text-slate-400 text-lg">Responda a algumas perguntas situacionais e deixe nossa IA mapear sua
          personalidade profissional usando métricas DISC e Big Five.</p>
      </div>
      <button @click="startQuiz"
        class="bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-4 px-10 rounded-2xl transition-all shadow-xl shadow-indigo-600/20 transform hover:-translate-y-1">
        Iniciar Mapeamento
      </button>
    </div>

    <div v-else-if="step === 1" class="max-w-2xl mx-auto w-full space-y-8 animate-slide-up">
      <div class="flex justify-between items-end mb-2">
        <span class="text-indigo-400 font-bold uppercase tracking-widest text-xs">Pergunta {{ currentQuestionIndex + 1
          }} de {{ questions.length }}</span>
        <div class="h-2 w-32 bg-white/5 rounded-full overflow-hidden">
          <div class="h-full bg-indigo-500 transition-all duration-500"
            :style="{ width: ((currentQuestionIndex + 1) / questions.length) * 100 + '%' }"></div>
        </div>
      </div>
      <h2 class="text-2xl font-bold text-white leading-tight">{{ questions[currentQuestionIndex].text }}</h2>
      <div class="grid gap-4">
        <button v-for="opt in questions[currentQuestionIndex].options" :key="opt" @click="nextQuestion(opt)"
          class="w-full text-left p-5 rounded-2xl bg-white/5 border border-white/10 text-slate-300 hover:bg-indigo-600/20 hover:border-indigo-500/50 hover:text-white transition-all duration-300">
          {{ opt }}
        </button>
      </div>
    </div>

    <div v-else-if="step === 2 && profile" class="space-y-8 animate-fade-in">
      <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 class="text-3xl font-black text-white">{{ profile.arquétipo }}</h2>
          <p class="text-indigo-400 font-medium tracking-wide uppercase text-sm">Perfil Profissional Detalhado</p>
        </div>
        <button @click="resetTest" class="text-slate-500 hover:text-red-400 text-sm font-bold transition-colors">REFazer
          teste</button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-1 bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-6">
          <h3 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-6">Equilíbrio DISC</h3>

          <apexchart v-if="profile && profile.disc" type="radar" height="300" :options="chartOptions"
            :series="chartSeries"></apexchart>
        </div>

        <div class="lg:col-span-2 space-y-6">
          <div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8">
            <h3 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Análise da IA</h3>
            <p class="text-slate-300 leading-relaxed text-lg italic">"{{ profile.resumo }}"</p>
            <div class="mt-6 flex flex-wrap gap-2">
              <span v-for="tag in profile.inteligencias_principais" :key="tag"
                class="px-4 py-1.5 bg-indigo-500/20 text-indigo-400 rounded-full text-xs font-bold border border-indigo-500/30">
                {{ tag }}
              </span>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-emerald-500/5 border border-emerald-500/10 rounded-3xl p-6">
              <h4 class="text-emerald-400 font-bold mb-4 text-sm uppercase">Pontos Fortes</h4>
              <ul class="space-y-3">
                <li v-for="p in profile.pontos_fortes" :key="p" class="flex items-center gap-3 text-slate-300 text-sm">
                  <div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div> {{ p }}
                </li>
              </ul>
            </div>
            <div class="bg-orange-500/5 border border-orange-500/10 rounded-3xl p-6">
              <h4 class="text-orange-400 font-bold mb-4 text-sm uppercase">A Desenvolver</h4>
              <ul class="space-y-3">
                <li v-for="p in profile.pontos_desenvolvimento" :key="p"
                  class="flex items-center gap-3 text-slate-300 text-sm">
                  <div class="w-1.5 h-1.5 rounded-full bg-orange-500"></div> {{ p }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.8s ease-out;
}

.animate-slide-up {
  animation: slideUp 0.6s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>