const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const CompanyInsight = sequelize.define('CompanyInsight', {
  id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true },
  dominio: { type: DataTypes.STRING, unique: true, allowNull: false },
  nome_empresa: { type: DataTypes.STRING, allowNull: false },
  dados_brutos_pesquisa: { type: DataTypes.JSON, allowNull: true },
  tech_stack_identificada: { type: DataTypes.JSON, allowNull: true }
}, {
  tableName: 'company_insights',
  timestamps: true
});

module.exports = CompanyInsight;