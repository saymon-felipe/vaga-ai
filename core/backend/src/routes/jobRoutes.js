const express = require('express');
const JobApplication = require('../models/JobApplication');
const CompanyInsight = require('../models/CompanyInsight');

const router = express.Router();

router.get('/jobs/status', async (req, res) => {
  try {
    // 1. Busca as vagas mais recentes no banco
    const jobs = await JobApplication.findAll({
      order: [['createdAt', 'DESC']]
    });

    // 2. Pergunta ao Worker (no Windows) se ele ainda está rodando
    let isWorkerRunning = false;
    try {
      const workerResponse = await fetch('http://host.docker.internal:8001/api/status');
      if (workerResponse.ok) {
        const workerData = await workerResponse.json();
        isWorkerRunning = workerData.is_running;
      }
    } catch (err) {
      console.log('-> [NODE] Aviso: Worker offline ou inatingível.');
    }

    // 3. Devolve tudo mastigado para o Frontend
    res.json({ 
      isRunning: isWorkerRunning, 
      jobs: jobs 
    });
  } catch (error) {
    res.status(500).json({ error: 'Erro ao buscar status das vagas.' });
  }
});

router.post('/jobs/start', async (req, res) => {
  const { cargo, localizacao } = req.body;
  console.log(`-> [NODE] Mandando sinal para INICIAR o Worker no Windows...`);

  try {
    // [MUDANÇA] Aponta para a máquina local do Windows em vez do container
    const response = await fetch('http://host.docker.internal:8001/api/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cargo, localizacao })
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: 'Falha de comunicação com o Worker.' });
  }
});

router.post('/jobs/stop', async (req, res) => {
  console.log(`-> [NODE] Mandando sinal para PARAR o Worker no Windows...`);

  try {
    // [MUDANÇA] Aponta para a máquina local do Windows
    const response = await fetch('http://host.docker.internal:8001/api/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: 'Falha de comunicação com o Worker.' });
  }
});

module.exports = router;