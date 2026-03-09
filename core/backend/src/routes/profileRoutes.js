const express = require('express');
const multer = require('multer');
const Profile = require('../models/Profile');
const uploadToS3 = require('../utils/s3Upload');

const router = express.Router();
const upload = multer({ storage: multer.memoryStorage() });

router.get('/profile', async (req, res) => {
  // [MUDANÇA] Rastreadores para ver em qual linha exata o código pode estar travando
  console.log('-> [GET] Recebeu chamada em /api/profile');
  try {
    console.log('-> [GET] Iniciando busca no banco de dados...');
    const profile = await Profile.findOne();
    console.log('-> [GET] Retorno do banco:', profile ? 'Encontrado' : 'Vazio');
    
    if (profile) {
      return res.json({
        nome: profile.nome,
        email: profile.email,
        telefone: profile.telefone,
        nivel: profile.nivel,
        fotoUrl: profile.foto_url,
        curriculoUrl: profile.curriculo_url
      });
    }
    return res.json({});
  } catch (error) {
    console.error('-> [GET] Erro fatal:', error);
    res.status(500).json({ error: 'Erro interno ao buscar perfil' });
  }
});

router.post('/profile/completo', upload.fields([
  { name: 'foto', maxCount: 1 },
  { name: 'curriculo', maxCount: 1 }
]), async (req, res) => {
  console.log('-> [POST] Recebeu dados para salvar perfil');
  try {
    const { nome, email, telefone, nivel } = req.body;
    const fotoFile = req.files['foto'] ? req.files['foto'][0] : null;
    const curriculoFile = req.files['curriculo'] ? req.files['curriculo'][0] : null;

    const fotoUrl = await uploadToS3(fotoFile, 'fotos');
    const curriculoUrl = await uploadToS3(curriculoFile, 'curriculos');

    const profileData = { nome, email, telefone, nivel };
    if (fotoUrl) profileData.foto_url = fotoUrl;
    if (curriculoUrl) profileData.curriculo_url = curriculoUrl;

    let profile = await Profile.findOne({ where: { email } });
    
    if (profile) {
      await profile.update(profileData);
    } else {
      profile = await Profile.create(profileData);
    }

    console.log('-> [POST] Perfil salvo com sucesso!');
    res.json({ id: profile.id, status: 'sucesso', dados: profileData });
  } catch (error) {
    console.error('-> [POST] Erro ao salvar:', error);
    res.status(500).json({ error: 'Erro ao salvar perfil' });
  }
});

module.exports = router;