const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const JobApplication = sequelize.define('JobApplication', {
  id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
  plataforma: { type: DataTypes.STRING, allowNull: false },
  empresa_nome: { type: DataTypes.STRING, allowNull: false },
  vaga_titulo: { type: DataTypes.STRING, allowNull: false },
  vaga_url: { type: DataTypes.TEXT, allowNull: false },
  status: {
    type: DataTypes.STRING,
    defaultValue: 'Analisando'
  },
  applied: {
    type: DataTypes.BOOLEAN,
    defaultValue: false
  },
  match_score: { type: DataTypes.INTEGER, allowNull: true },
  job_description_raw: { type: DataTypes.TEXT, allowNull: true },
  respostas_ia_raw: { type: DataTypes.JSON, allowNull: true },
  argumentos_match_raw: { type: DataTypes.JSON, allowNull: true },
  faixa_salarial: {
    type: DataTypes.STRING,
    defaultValue: 'A Combinar'
  },
  requer_confirmacao_email: {
    type: DataTypes.BOOLEAN,
    defaultValue: false
  }
}, {
  tableName: 'job_applications',
  timestamps: true
});

module.exports = JobApplication;