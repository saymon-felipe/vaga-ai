const express = require('express');
const BehavioralProfile = require('../models/BehavioralProfile');
const { analyzeBehavioralProfile } = require('../utils/aiAnalyzer');

const router = express.Router();

router.get('/behavioral', async (req, res) => {
  try {
    const profile = await BehavioralProfile.findOne({
      order: [['createdAt', 'DESC']]
    });
    
    if (profile) {
      return res.json(profile);
    }
    return res.json(null);
  } catch (error) {
    res.status(500).json({ error: 'Erro ao buscar perfil comportamental' });
  }
});

router.post('/behavioral/analyze', async (req, res) => {
  try {
    const { answers } = req.body;
    
    if (!answers || Object.keys(answers).length === 0) {
      return res.status(400).json({ error: 'Respostas inválidas' });
    }

    const aiResult = await analyzeBehavioralProfile(answers);

    await BehavioralProfile.destroy({ truncate: true });

    const newProfile = await BehavioralProfile.create({
      raw_answers: answers,
      ai_analysis: aiResult
    });

    res.json(newProfile);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Erro ao analisar e salvar perfil' });
  }
});

router.delete('/behavioral', async (req, res) => {
  try {
    await BehavioralProfile.destroy({ truncate: true });
    res.json({ status: 'sucesso' });
  } catch (error) {
    res.status(500).json({ error: 'Erro ao deletar perfil comportamental' });
  }
});

module.exports = router;