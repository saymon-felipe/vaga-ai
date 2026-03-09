<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const trajetoria = ref([])
const carregando = ref(true)

// Estado do Formulário
const novoItem = ref({
  tipo: 'Profissional',
  instituicao: '',
  cargo_curso: '',
  descricao: '',
  data_inicio: '',
  data_fim: '',
  atual: false
})

const aprimorandoComIA = ref(false);
const backupDescricao = ref('');

const aprimorarTexto = async () => {
  if (!novoItem.value.descricao || novoItem.value.descricao.length < 5) {
    alert("Escreva a base da descrição primeiro para que a IA possa aprimorar.");
    return;
  }

  // Salva o texto atual antes de chamar a IA
  backupDescricao.value = novoItem.value.descricao;

  aprimorandoComIA.value = true;
  try {
    const response = await api.post('/trajectory/refine', {
      texto: novoItem.value.descricao,
      cargo_curso: novoItem.value.cargo_curso,
      tipo: novoItem.value.tipo
    });

    novoItem.value.descricao = response.data.textoAprimorado;
  } catch (error) {
    alert("Erro ao conectar com a IA.");
    backupDescricao.value = ''; // Limpa o backup em caso de erro
  } finally {
    aprimorandoComIA.value = false;
  }
};

// Função para restaurar o texto anterior
const restaurarOriginal = () => {
  if (backupDescricao.value) {
    novoItem.value.descricao = backupDescricao.value;
    backupDescricao.value = ''; // Limpa o backup após restaurar
  }
};

const carregarTrajetoria = async () => {
  try {
    const response = await api.get('/trajectory')
    trajetoria.value = response.data
  } catch (error) {
    console.error("Erro ao carregar trajetória:", error)
  } finally {
    carregando.value = false
  }
}

const salvarItem = async () => {
  try {
    const dadosParaEnviar = { ...novoItem.value }
    if (dadosParaEnviar.atual) dadosParaEnviar.data_fim = null

    const response = await api.post('/trajectory', dadosParaEnviar)
    trajetoria.value.unshift(response.data)

    // Resetar formulário
    novoItem.value = { tipo: 'Profissional', instituicao: '', cargo_curso: '', descricao: '', data_inicio: '', data_fim: '', atual: false }
  } catch (error) {
    alert("Erro ao salvar item.")
  }
}

const excluirItem = async (id) => {
  if (!confirm("Excluir este registro?")) return
  try {
    await api.delete(`/trajectory/${id}`)
    trajetoria.value = trajetoria.value.filter(i => i.id !== id)
  } catch (error) {
    console.error(error)
  }
}

const formatarData = (data) => {
  if (!data) return 'Atual'
  return new Date(data).toLocaleDateString('pt-BR', { month: 'short', year: 'numeric' })
}

onMounted(carregarTrajetoria)
</script>

<template>
  <div class="max-w-5xl mx-auto p-6 space-y-12">

    <div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
      <h2 class="text-xl font-bold text-white mb-6 flex items-center gap-2">
        <span class="w-2 h-6 bg-indigo-500 rounded-full"></span>
        Adicionar Experiência ou Formação
      </h2>

      <form @submit.prevent="salvarItem" class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="md:col-span-2 flex bg-slate-800/50 p-1 rounded-xl w-fit">
          <button v-for="t in ['Profissional', 'Acadêmica']" :key="t" type="button" @click="novoItem.tipo = t"
            :class="novoItem.tipo === t ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'"
            class="px-6 py-2 rounded-lg text-sm font-bold transition-all">
            {{ t }}
          </button>
        </div>

        <div class="space-y-2">
          <label class="text-xs font-bold text-slate-400 uppercase tracking-wider">{{ novoItem.tipo === 'Profissional' ?
            'Empresa' : 'Instituição' }}</label>
          <input v-model="novoItem.instituicao" type="text" required
            class="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-indigo-500">
        </div>

        <div class="space-y-2">
          <label class="text-xs font-bold text-slate-400 uppercase tracking-wider">{{ novoItem.tipo === 'Profissional' ?
            'Cargo' : 'Curso' }}</label>
          <input v-model="novoItem.cargo_curso" type="text" required
            class="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-indigo-500">
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <label class="text-xs font-bold text-slate-400 uppercase tracking-wider">Início</label>
            <input v-model="novoItem.data_inicio" type="date" required
              class="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white outline-none">
          </div>
          <div class="space-y-2" v-if="!novoItem.atual">
            <label class="text-xs font-bold text-slate-400 uppercase tracking-wider">Fim</label>
            <input v-model="novoItem.data_fim" type="date"
              class="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white outline-none">
          </div>
          <div v-else class="flex items-end pb-4">
            <span class="text-indigo-400 font-bold text-sm">Trabalhando aqui atualmente</span>
          </div>
        </div>

        <div class="flex items-center gap-2 pt-8">
          <input type="checkbox" v-model="novoItem.atual" id="atual"
            class="w-4 h-4 rounded border-white/10 bg-slate-900">
          <label for="atual" class="text-sm text-slate-300">Este é meu cargo/curso atual</label>
        </div>

        <div class="md:col-span-2 space-y-2">
          <div class="flex justify-between items-end">
            <label class="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Descrição / Conquistas
            </label>

            <div class="flex gap-2">
              <button v-if="backupDescricao && !aprimorandoComIA" type="button" @click="restaurarOriginal"
                class="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-lg border border-white/10 bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white transition-all cursor-pointer">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"></path>
                </svg>
                Desfazer IA
              </button>

              <button type="button" @click="aprimorarTexto" :disabled="aprimorandoComIA"
                class="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-lg border border-indigo-500/30 bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500 hover:text-white transition-all disabled:opacity-50 cursor-pointer">
                <div v-if="aprimorandoComIA"
                  class="w-3.5 h-3.5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin"></div>
                <svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z">
                  </path>
                </svg>
                {{ aprimorandoComIA ? 'Aprimorando...' : 'Aprimorar com IA' }}
              </button>
            </div>
          </div>

          <textarea v-model="novoItem.descricao" rows="4"
            class="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-indigo-500 transition-all"></textarea>
        </div>

        <button type="submit"
          class="md:col-span-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-indigo-600/20">
          Salvar na Trajetória
        </button>
      </form>
    </div>

    <div class="relative px-4">
      <div
        class="absolute left-4 md:left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-indigo-500 via-purple-500 to-transparent">
      </div>

      <div class="space-y-12">
        <div v-for="(item, index) in trajetoria" :key="item.id" class="relative flex flex-col md:flex-row items-center"
          :class="index % 2 === 0 ? 'md:flex-row-reverse' : ''">
          <div
            class="absolute left-3 md:left-1/2 w-3 h-3 bg-white rounded-full transform -translate-x-1/2 z-10 shadow-[0_0_15px_rgba(255,255,255,0.8)]">
          </div>

          <div
            class="w-full md:w-[45%] ml-10 md:ml-0 bg-white/5 border border-white/10 p-6 rounded-2xl backdrop-blur-md hover:bg-white/10 transition-all group">
            <div class="flex justify-between items-start mb-4">
              <span
                :class="item.tipo === 'Profissional' ? 'text-blue-400 bg-blue-400/10' : 'text-purple-400 bg-purple-400/10'"
                class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border border-current">
                {{ item.tipo }}
              </span>
              <button @click="excluirItem(item.id)"
                class="text-slate-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16">
                  </path>
                </svg>
              </button>
            </div>

            <h3 class="text-xl font-bold text-white">{{ item.cargo_curso }}</h3>
            <p class="text-indigo-400 font-medium mb-2">{{ item.instituicao }}</p>
            <p class="text-xs text-slate-500 font-mono mb-4 uppercase">
              {{ formatarData(item.data_inicio) }} — {{ item.atual ? 'Presente' : formatarData(item.data_fim) }}
            </p>
            <p class="text-slate-400 text-sm leading-relaxed">{{ item.descricao }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Esconder scrollbar do dropdown mas manter funcionalidade */
.no-scrollbar::-webkit-scrollbar {
  display: none;
}

.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>