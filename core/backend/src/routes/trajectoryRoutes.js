const express = require('express');
const Trajectory = require('../models/Trajectory');
const router = express.Router();
const { OpenAI } = require('openai');
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

router.post('/trajectory/refine', async (req, res) => {
  const { texto, cargo_curso, tipo } = req.body;

  if (!texto || texto.length < 5) {
    return res.status(400).json({ error: 'Escreva um pouco mais para que a IA possa ajudar.' });
  }

  const prompt = `
    Atue como um especialista em recrutamento e seleção (Tech Recruiter).
    Aprimore a seguinte descrição de uma experiência ${tipo} (${cargo_curso}):
    
    Texto original: "${texto}"
    
    Regras:
    1. Torne o texto mais profissional e impactante.
    2. Use verbos de ação.
    3. Mantenha o texto conciso (máximo 3 parágrafos ou lista de bullets).
    4. Retorne APENAS o texto aprimorado, sem introduções ou explicações.
    5. Retorne o texto em primeira pessoa, ex: Projetei, desenvolvi, implementei, etc.
    6. Retorne texto humanizado, sem parecer que foi escrito por IA.
  `;

  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4.1-nano',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.7,
    });

    res.json({ textoAprimorado: response.choices[0].message.content.trim() });
  } catch (error) {
    console.error('Erro na IA:', error);
    res.status(500).json({ error: 'Falha ao aprimorar texto.' });
  }
});

// Listar toda a trajetória ordenada pela data mais recente
router.get('/trajectory', async (req, res) => {
  try {
    const items = await Trajectory.findAll({
      order: [['data_inicio', 'DESC']]
    });
    res.json(items);
  } catch (error) {
    res.status(500).json({ error: 'Erro ao buscar trajetória' });
  }
});

// Adicionar novo item à trajetória
router.post('/trajectory', async (req, res) => {
  try {
    const novoItem = await Trajectory.create(req.body);
    res.json(novoItem);
  } catch (error) {
    res.status(500).json({ error: 'Erro ao salvar item na trajetória' });
  }
});

// Eliminar um item
router.delete('/trajectory/:id', async (req, res) => {
  try {
    await Trajectory.destroy({ where: { id: req.params.id } });
    res.json({ status: 'sucesso' });
  } catch (error) {
    res.status(500).json({ error: 'Erro ao eliminar item' });
  }
});

module.exports = router;