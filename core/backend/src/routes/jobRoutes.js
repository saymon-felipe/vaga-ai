const express = require('express');
const JobApplication = require('../models/JobApplication');
const CompanyInsight = require('../models/CompanyInsight');

const router = express.Router();

router.get('/jobs/status', async (req, res) => {
  try {
    const jobs = await JobApplication.findAll({
      order: [['createdAt', 'DESC']]
    });
    res.json(jobs);
  } catch (error) {
    res.status(500).json({ error: 'Erro ao buscar status das vagas.' });
  }
});

router.post('/jobs/start', async (req, res) => {
  const { cargo, localizacao } = req.body;
  console.log(`-> [NODE] Mandando sinal para INICIAR o Worker Python...`);

  try {
    const response = await fetch('http://worker:8001/api/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cargo, localizacao })
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('-> [NODE] Erro ao acordar o Worker:', error.message);
    res.status(500).json({ error: 'Falha de comunicação com o Worker.' });
  }
});

// [NOVO] Rota para parar a automação
router.post('/jobs/stop', async (req, res) => {
  console.log(`-> [NODE] Mandando sinal para PARAR o Worker Python...`);

  try {
    const response = await fetch('http://worker:8001/api/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('-> [NODE] Erro ao parar o Worker:', error.message);
    res.status(500).json({ error: 'Falha de comunicação com o Worker.' });
  }
});

module.exports = router;