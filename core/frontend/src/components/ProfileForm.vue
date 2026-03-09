<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
// [MUDANÇA] Importando a instância configurada do Axios
import api from '../services/api'

const profileData = ref({
  nome: 'Usuário Padrão',
  email: 'usuario@vagaai.com',
  nivel: 'Desenvolvedor Pleno',
  fotoUrl: 'https://ui-avatars.com/api/?name=Usuário+Padrão&background=6366f1&color=fff&size=128'
})

const profileForm = ref({
  nome: '',
  email: '',
  telefone: '',
  nivel: ''
})

const fotoFile = ref(null)
const curriculoFile = ref(null)
const previewAvatar = ref(profileData.value.fotoUrl)
const previewPdf = ref(null)
const isSubmitting = ref(false)
const submitMessage = ref('')

// [MUDANÇA] Utilizando api.get e response.data
const carregarDadosDoBanco = async () => {
  try {
    const response = await api.get('/profile')
    const data = response.data

    if (data.nome) {
      profileData.value.nome = data.nome
      profileData.value.email = data.email
      profileData.value.nivel = data.nivel || 'Nível não definido'
      
      if (data.fotoUrl) {
        profileData.value.fotoUrl = data.fotoUrl
        previewAvatar.value = data.fotoUrl
      }

      profileForm.value.nome = data.nome
      profileForm.value.email = data.email
      profileForm.value.telefone = data.telefone || ''
      profileForm.value.nivel = data.nivel || ''

      if (data.curriculoUrl) {
        previewPdf.value = data.curriculoUrl
      }
    }
  } catch (error) {
    console.error('Falha ao carregar perfil', error)
  }
}

onMounted(() => {
  carregarDadosDoBanco()
})

const handleFileUpload = (event, type) => {
  const file = event.target.files[0]
  if (!file) return

  if (type === 'curriculo') {
    if (file.size > 2 * 1024 * 1024) {
      alert('O currículo deve ter no máximo 2MB.')
      event.target.value = ''
      curriculoFile.value = null
      return
    }
    curriculoFile.value = file
    
    if (previewPdf.value && !previewPdf.value.includes('s3.amazonaws')) {
      URL.revokeObjectURL(previewPdf.value)
    }
    previewPdf.value = URL.createObjectURL(file)
  }

  if (type === 'foto') {
    fotoFile.value = file
    
    if (previewAvatar.value !== profileData.value.fotoUrl && !previewAvatar.value.includes('s3.amazonaws')) {
      URL.revokeObjectURL(previewAvatar.value)
    }
    previewAvatar.value = URL.createObjectURL(file)
  }
}

const submitProfile = async () => {
  isSubmitting.value = true
  submitMessage.value = ''

  const formData = new FormData()
  formData.append('nome', profileForm.value.nome)
  formData.append('email', profileForm.value.email)
  formData.append('telefone', profileForm.value.telefone)
  formData.append('nivel', profileForm.value.nivel)
  
  if (fotoFile.value) formData.append('foto', fotoFile.value)
  if (curriculoFile.value) formData.append('curriculo', curriculoFile.value)

  try {
    // [MUDANÇA] Utilizando api.post com headers para multipart/form-data
    const response = await api.post('/profile/completo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.status === 200) {
      submitMessage.value = 'Perfil atualizado com sucesso!'
      profileData.value.nome = profileForm.value.nome
      profileData.value.email = profileForm.value.email
      profileData.value.nivel = profileForm.value.nivel
      if (fotoFile.value) profileData.value.fotoUrl = previewAvatar.value
      
      const responseData = response.data
      if (responseData.dados.curriculo_url) {
        previewPdf.value = responseData.dados.curriculo_url
      }

    } else {
      submitMessage.value = 'Erro ao salvar o perfil.'
    }
  } catch (error) {
    submitMessage.value = 'Erro de conexão com a API.'
  } finally {
    isSubmitting.value = false
    setTimeout(() => submitMessage.value = '', 5000)
  }
}

onUnmounted(() => {
  if (previewPdf.value && !previewPdf.value.includes('s3.amazonaws')) {
    URL.revokeObjectURL(previewPdf.value)
  }
  if (previewAvatar.value !== profileData.value.fotoUrl && !previewAvatar.value.includes('s3.amazonaws')) {
    URL.revokeObjectURL(previewAvatar.value)
  }
})
</script>

<template>
  <div class="max-w-6xl space-y-6">
    
    <div class="bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-8 relative overflow-hidden flex items-center gap-8 shadow-2xl">
      <div class="absolute top-[-50%] right-[-10%] w-96 h-96 bg-indigo-500/20 rounded-full blur-[100px] pointer-events-none"></div>
      
      <div class="relative z-10 flex-shrink-0">
        <div class="w-28 h-28 rounded-full p-1 bg-gradient-to-br from-indigo-500 to-purple-600 shadow-[0_0_30px_rgba(99,102,241,0.4)]">
          <img :src="previewAvatar" alt="Avatar" class="w-full h-full object-cover rounded-full border-4 border-slate-900" />
        </div>
      </div>
      
      <div class="relative z-10 flex-1">
        <h2 class="text-3xl font-extrabold text-white tracking-tight">{{ profileData.nome }}</h2>
        <p class="text-slate-400 font-medium mt-1 flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
          {{ profileData.email }}
        </p>
        <div class="mt-4 inline-flex items-center px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-bold uppercase tracking-widest shadow-inner">
          <span class="w-2 h-2 rounded-full bg-indigo-400 mr-2 animate-pulse"></span>
          {{ profileData.nivel }}
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
      
      <div class="lg:col-span-3 bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-8 relative shadow-xl">
        <h3 class="text-sm font-semibold text-slate-300 uppercase tracking-widest mb-6 flex items-center gap-3">
          Configurações da Conta
        </h3>

        <form @submit.prevent="submitProfile" class="space-y-6">
          <transition name="fade">
            <div v-if="submitMessage" :class="[
              'p-4 rounded-xl text-sm font-medium border backdrop-blur-sm transition-all', 
              submitMessage.includes('Erro') ? 'bg-red-500/10 border-red-500/20 text-red-400' : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
            ]">
              {{ submitMessage }}
            </div>
          </transition>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="md:col-span-2">
              <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Nome Completo</label>
              <input v-model="profileForm.nome" type="text" required class="w-full bg-slate-800/50 border border-white/10 text-white placeholder-slate-500 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all">
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">E-mail</label>
              <input v-model="profileForm.email" type="email" required class="w-full bg-slate-800/50 border border-white/10 text-white placeholder-slate-500 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all">
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">WhatsApp / Telefone</label>
              <input v-model="profileForm.telefone" type="text" class="w-full bg-slate-800/50 border border-white/10 text-white placeholder-slate-500 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all">
            </div>

            <div class="md:col-span-2">
              <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Nível / Senioridade</label>
              <select v-model="profileForm.nivel" class="w-full bg-slate-800/50 border border-white/10 text-white rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all appearance-none cursor-pointer">
                <option value="Estagiário">Estagiário</option>
                <option value="Desenvolvedor Júnior">Desenvolvedor Júnior</option>
                <option value="Desenvolvedor Pleno">Desenvolvedor Pleno</option>
                <option value="Desenvolvedor Sênior">Desenvolvedor Sênior</option>
                <option value="Especialista / Tech Lead">Especialista / Tech Lead</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 border-t border-white/5">
            <div>
              <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Alterar Foto</label>
              <div class="relative group h-14">
                <input @change="e => handleFileUpload(e, 'foto')" type="file" accept="image/*" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10">
                <div class="w-full h-full bg-slate-800/30 border border-dashed border-white/20 group-hover:border-indigo-500/50 rounded-xl flex items-center justify-center transition-all group-hover:bg-indigo-500/5">
                  <span class="text-sm text-slate-400 group-hover:text-indigo-400 truncate px-4">
                    {{ fotoFile ? fotoFile.name : 'Procurar imagem...' }}
                  </span>
                </div>
              </div>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Upload de Currículo (PDF)</label>
              <div class="relative group h-14">
                <input @change="e => handleFileUpload(e, 'curriculo')" type="file" accept="application/pdf" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10">
                <div class="w-full h-full bg-slate-800/30 border border-dashed border-white/20 group-hover:border-purple-500/50 rounded-xl flex items-center justify-center transition-all group-hover:bg-purple-500/5">
                  <span class="text-sm text-slate-400 group-hover:text-purple-400 truncate px-4">
                    {{ curriculoFile ? curriculoFile.name : 'Selecionar arquivo PDF...' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <button type="submit" :disabled="isSubmitting" class="w-full mt-4 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:shadow-[0_0_30px_rgba(168,85,247,0.5)] disabled:opacity-50 disabled:cursor-not-allowed transform hover:-translate-y-0.5">
            {{ isSubmitting ? 'Processando...' : 'Salvar Alterações' }}
          </button>
        </form>
      </div>

      <div class="lg:col-span-2 bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-6 flex flex-col h-[650px] shadow-xl">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-slate-300 uppercase tracking-widest">
            Prévia do Currículo
          </h3>
          <span v-if="previewPdf" class="px-2 py-1 bg-emerald-500/10 text-emerald-400 text-[10px] font-bold uppercase rounded border border-emerald-500/20">Pronto</span>
        </div>
        
        <div class="flex-1 bg-slate-900/80 rounded-2xl border border-white/5 overflow-hidden flex items-center justify-center relative shadow-inner">
          <iframe v-if="previewPdf" :src="previewPdf" class="w-full h-full border-0 absolute inset-0"></iframe>
          
          <div v-else class="text-center p-6">
            <div class="w-16 h-16 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-4 border border-white/5">
              <svg class="w-8 h-8 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
            </div>
            <p class="text-slate-400 text-sm font-medium">Nenhum currículo selecionado.</p>
            <p class="text-slate-500 text-xs mt-2">Faça o upload do seu PDF para visualizá-lo aqui.</p>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>