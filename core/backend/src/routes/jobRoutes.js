const express = require('express');
const JobApplication = require('../models/JobApplication');
const CompanyInsight = require('../models/CompanyInsight');

const router = express.Router();

router.get('/jobs/status', async (req, res) => {
  try {
    const jobs = await JobApplication.findAll({
      order: [['createdAt', 'DESC']]
    });

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

    res.json({ 
      isRunning: isWorkerRunning, 
      jobs: jobs 
    });
  } catch (error) {
    res.status(500).json({ error: 'Erro ao buscar status das vagas.' });
  }
});

router.put('/jobs/:id/applied', async (req, res) => {
  try {
    const { id } = req.params;
    const { applied } = req.body;
    
    const job = await JobApplication.findByPk(id);
    if (!job) {
      return res.status(404).json({ error: 'Vaga não encontrada' });
    }
    
    job.applied = applied;
    await job.save();
    
    res.json(job);
  } catch (error) {
    console.error('Erro ao atualizar status de aplicação:', error);
    res.status(500).json({ error: 'Erro interno ao atualizar aplicação' });
  }
});

router.get('/jobs/notifications', async (req, res) => {
  try {
    const notifications = await JobApplication.findAll({
      where: { requer_confirmacao_email: true, status: 'Aplicado' },
      order: [['createdAt', 'DESC']]
    });
    res.json(notifications);
  } catch (error) {
    res.status(500).json({ error: 'Erro ao buscar notificações.' });
  }
});

router.put('/jobs/:id/confirm-email', async (req, res) => {
  try {
    const { id } = req.params;
    await JobApplication.update(
      { requer_confirmacao_email: false },
      { where: { id } }
    );
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: 'Erro ao atualizar status do e-mail.' });
  }
});

router.post('/jobs/start', async (req, res) => {
  const { cargo, localizacao } = req.body;
  console.log(`-> [NODE] Mandando sinal para INICIAR o Worker no Windows...`);

  try {
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