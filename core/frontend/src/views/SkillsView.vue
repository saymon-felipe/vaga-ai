<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../services/api'

const niveis = ['Básico', 'Intermediário', 'Avançado']
const skills = ref([])

// [MUDANÇA] Configuração estrutural das 3 seções
const secoes = [
  { id: 'Soft Skill', titulo: 'Soft Skills', cor: 'indigo', opcoes: ['Comunicação', 'Liderança', 'Resolução de Problemas', 'Trabalho em Equipe', 'Inteligência Emocional', 'Adaptabilidade', 'Gestão de Tempo', 'Criatividade', 'Negociação'] },
  { id: 'Hard Skill', titulo: 'Hard Skills', cor: 'purple', opcoes: ['Análise de Dados', 'Gestão de Projetos', 'Marketing Digital', 'Contabilidade', 'Engenharia de Software', 'Design UI/UX', 'SEO', 'Scrum / Ágil', 'Copywriting'] },
  { id: 'Tech Stack', titulo: 'Stacks Técnicas', cor: 'emerald', opcoes: ['JavaScript', 'Python', 'Java', 'C#', 'Vue.js', 'React', 'Node.js', 'Docker', 'AWS', 'SQL', 'MongoDB', 'TypeScript', 'Git'] }
]

// [MUDANÇA] Estado reativo independente para cada formulário da seção
const formStates = ref({
  'Soft Skill': { busca: '', nivel: 'Intermediário', isOpen: false },
  'Hard Skill': { busca: '', nivel: 'Intermediário', isOpen: false },
  'Tech Stack': { busca: '', nivel: 'Intermediário', isOpen: false }
})

const carregarSkills = async () => {
  try {
    const response = await api.get('/skills')
    skills.value = response.data
  } catch (error) {
    console.error(error)
  }
}

onMounted(() => {
  carregarSkills()
})

const filtrarOpcoes = (tipo) => {
  const query = formStates.value[tipo].busca.toLowerCase()
  const sec = secoes.find(s => s.id === tipo)
  return sec.opcoes.filter(opt => opt.toLowerCase().includes(query))
}

const selecionarOpcao = (tipo, valor) => {
  formStates.value[tipo].busca = valor
  formStates.value[tipo].isOpen = false
}

const fecharDropdown = (tipo) => {
  setTimeout(() => {
    formStates.value[tipo].isOpen = false
  }, 150)
}

const adicionarSkill = async (tipo) => {
  const nomeSkill = formStates.value[tipo].busca.trim()
  if (!nomeSkill) return
  
  try {
    const response = await api.post('/skills', {
      nome: nomeSkill,
      nivel: formStates.value[tipo].nivel,
      tipo: tipo // [MUDANÇA] Enviando o tipo para a API
    })
    
    skills.value.push(response.data)
    formStates.value[tipo].busca = ''
  } catch (error) {
    console.error(error)
  }
}

const removerSkill = async (id) => {
  try {
    await api.delete(`/skills/${id}`)
    skills.value = skills.value.filter(skill => skill.id !== id)
  } catch (error) {
    console.error(error)
  }
}

const skillsFiltradas = (tipo) => {
  return skills.value.filter(skill => skill.tipo === tipo)
}

const getNivelCores = (nivel, corBase) => {
  if (nivel === 'Avançado') return { texto: `text-${corBase}-400`, fundo: `bg-${corBase}-400/10`, borda: `border-${corBase}-400/20`, barra: `from-${corBase}-500 to-${corBase}-400` }
  if (nivel === 'Intermediário') return { texto: 'text-slate-300', fundo: 'bg-white/10', borda: 'border-white/20', barra: 'from-slate-400 to-slate-300' }
  return { texto: 'text-slate-500', fundo: 'bg-black/20', borda: 'border-white/5', barra: 'from-slate-600 to-slate-500' }
}

const getLarguraBarra = (nivel) => {
  if (nivel === 'Avançado') return '100%'
  if (nivel === 'Intermediário') return '66%'
  return '33%'
}
</script>

<template>
  <div class="max-w-6xl space-y-12 pb-12">
    
    <div v-for="secao in secoes" :key="secao.id" class="space-y-6">
      <div class="flex items-center gap-4 border-b border-white/10 pb-4">
        <div :class="`w-10 h-10 rounded-xl bg-gradient-to-br from-${secao.cor}-500 to-${secao.cor}-700 flex items-center justify-center shadow-lg shadow-${secao.cor}-500/30`">
          <svg v-if="secao.id === 'Soft Skill'" class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
          <svg v-if="secao.id === 'Hard Skill'" class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
          <svg v-if="secao.id === 'Tech Stack'" class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>
        </div>
        <h2 class="text-2xl font-bold text-white tracking-tight">{{ secao.titulo }}</h2>
      </div>

      <div class="bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-6 shadow-2xl transition-all duration-500 hover:bg-white/[0.07]">
        <form @submit.prevent="adicionarSkill(secao.id)" class="flex flex-col lg:flex-row gap-6 items-start lg:items-end">
          
          <div class="flex-1 w-full relative">
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Adicionar {{ secao.titulo }}</label>
            <input 
              v-model="formStates[secao.id].busca" 
              @focus="formStates[secao.id].isOpen = true"
              @blur="fecharDropdown(secao.id)"
              type="text" 
              placeholder="Digite para buscar ou adicionar nova..."
              class="w-full bg-slate-800/50 border border-white/10 text-white placeholder-slate-500 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all"
            >
            
            <transition name="fade">
              <div v-if="formStates[secao.id].isOpen" class="absolute z-50 w-full mt-2 bg-slate-800/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-[0_10px_40px_-10px_rgba(0,0,0,0.5)] overflow-hidden">
                <ul class="max-h-56 overflow-y-auto no-scrollbar py-2">
                  <li 
                    v-for="opt in filtrarOpcoes(secao.id)" 
                    :key="opt"
                    @mousedown.prevent="selecionarOpcao(secao.id, opt)"
                    class="px-4 py-3 text-slate-300 hover:bg-white/10 cursor-pointer hover:text-white cursor-pointer transition-colors"
                  >
                    {{ opt }}
                  </li>
                  
                  <li 
                    v-if="formStates[secao.id].busca && !filtrarOpcoes(secao.id).some(opt => opt.toLowerCase() === formStates[secao.id].busca.toLowerCase())"
                    @mousedown.prevent="selecionarOpcao(secao.id, formStates[secao.id].busca)"
                    class="px-4 py-3 text-indigo-400 hover:bg-indigo-500/20 cursor-pointer transition-colors flex items-center gap-2 border-t border-white/5 mt-1"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                    Adicionar "<span class="font-bold text-white">{{ formStates[secao.id].busca }}</span>"
                  </li>
                </ul>
              </div>
            </transition>
          </div>

          <div class="w-full lg:w-auto">
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Nível</label>
            <div class="flex bg-slate-800/50 border border-white/10 rounded-xl p-1">
              <button 
                v-for="nivel in niveis" 
                :key="nivel"
                type="button"
                @click="formStates[secao.id].nivel = nivel"
                class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300"
                :class="formStates[secao.id].nivel === nivel ? 'bg-white/10 text-white shadow-md' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'"
              >
                {{ nivel }}
              </button>
            </div>
          </div>

          <button 
            type="submit" 
            :disabled="!formStates[secao.id].busca"
            :class="`w-full lg:w-auto h-12 bg-gradient-to-r from-${secao.cor}-500 to-${secao.cor}-700 hover:from-${secao.cor}-400 hover:to-${secao.cor}-600 text-white font-bold px-8 rounded-xl transition-all shadow-[0_0_20px_rgba(0,0,0,0.3)] disabled:opacity-50 disabled:cursor-not-allowed transform hover:-translate-y-0.5 flex items-center justify-center gap-2`"
          >
            Adicionar
          </button>
        </form>

        <div class="mt-8">
          <div v-if="skillsFiltradas(secao.id).length === 0" class="text-center py-8 bg-white/5 border border-white/5 rounded-2xl border-dashed">
            <p class="text-slate-500 text-sm">Nenhuma habilidade listada nesta categoria.</p>
          </div>

          <transition-group name="list" tag="div" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div 
              v-for="skill in skillsFiltradas(secao.id)" 
              :key="skill.id" 
              class="group relative bg-slate-900/40 backdrop-blur-sm border border-white/5 rounded-xl p-5 overflow-hidden hover:bg-white/5 hover:border-white/10 transition-all duration-300"
            >
              <button 
                @click="removerSkill(skill.id)"
                class="absolute top-3 right-3 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              </button>

              <div class="flex flex-col gap-4">
                <div>
                  <h4 class="text-lg font-bold text-white mb-1.5 truncate pr-6">{{ skill.nome }}</h4>
                  <span 
                    class="inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border"
                    :class="[getNivelCores(skill.nivel, secao.cor).texto, getNivelCores(skill.nivel, secao.cor).fundo, getNivelCores(skill.nivel, secao.cor).borda]"
                  >
                    {{ skill.nivel }}
                  </span>
                </div>
                
                <div class="w-full bg-slate-800 rounded-full h-1 overflow-hidden">
                  <div 
                    class="h-full rounded-full transition-all duration-1000 bg-gradient-to-r"
                    :class="getNivelCores(skill.nivel, secao.cor).barra"
                    :style="{ width: getLarguraBarra(skill.nivel) }"
                  ></div>
                </div>
              </div>
            </div>
          </transition-group>
        </div>

      </div>
    </div>
    
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from {
  opacity: 0;
  transform: scale(0.9) translateY(10px);
}
.list-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(-10px);
}
.list-leave-active {
  position: absolute;
}
</style>