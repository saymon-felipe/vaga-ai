require('dotenv').config();
const express = require('express');
const cors = require('cors');
const sequelize = require('./src/config/database');
const profileRoutes = require('./src/routes/profileRoutes');
const skillRoutes = require('./src/routes/skillRoutes');
const behavioralRoutes = require('./src/routes/behavioralRoutes');
const trajectoryRoutes = require('./src/routes/trajectoryRoutes');

const app = express();

app.use(cors({
  origin: ['http://localhost:5173', 'http://127.0.0.1:5173', 'http://192.168.0.6:5173'],
  credentials: true
}));

app.use(express.json());

app.get('/ping', (req, res) => {
  console.log('-> Ping recebido com sucesso!');
  res.json({ status: 'ok', message: 'API Node.js respondendo perfeitamente!' });
});

app.use('/api', profileRoutes);
app.use('/api', skillRoutes);
app.use('/api', behavioralRoutes);
app.use('/api', trajectoryRoutes);

sequelize.sync({ alter: true }).then(() => {
  app.listen(8000, '0.0.0.0', () => {
    console.log('Node.js API inicializada com sucesso na porta 8000 (0.0.0.0).');
  });
}).catch(err => {
  console.error('Falha ao conectar com o banco de dados:', err);
});