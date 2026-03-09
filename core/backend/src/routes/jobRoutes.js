const express = require('express');
const router = express.Router();

router.post('/jobs/start', async (req, res) => {
  const { cargo, localizacao } = req.body;
  console.log(`-> [NODE] Mandando sinal para acordar o Worker Python...`);

  try {
    // Comunica com o Python através do nome do serviço no docker-compose ('worker')
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

module.exports = router;