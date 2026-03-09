const express = require('express');
const Skill = require('../models/Skill');

const router = express.Router();

router.get('/skills', async (req, res) => {
  try {
    const skills = await Skill.findAll();
    res.json(skills);
  } catch (error) {
    res.status(500).json({ error: 'Erro ao buscar skills' });
  }
});

router.post('/skills', async (req, res) => {
  try {
    // [MUDANÇA] Extraindo o tipo do corpo da requisição
    const { nome, nivel, tipo } = req.body;
    const novaSkill = await Skill.create({ nome, nivel, tipo });
    res.json(novaSkill);
  } catch (error) {
    res.status(500).json({ error: 'Erro ao adicionar skill' });
  }
});

router.delete('/skills/:id', async (req, res) => {
  try {
    const { id } = req.params;
    await Skill.destroy({ where: { id } });
    res.json({ status: 'sucesso' });
  } catch (error) {
    res.status(500).json({ error: 'Erro ao deletar skill' });
  }
});

module.exports = router;