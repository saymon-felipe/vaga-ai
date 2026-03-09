const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Trajectory = sequelize.define('Trajectory', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  tipo: {
    type: DataTypes.ENUM('Profissional', 'Acadêmica'),
    allowNull: false
  },
  instituicao: {
    type: DataTypes.STRING,
    allowNull: false
  },
  cargo_curso: {
    type: DataTypes.STRING,
    allowNull: false
  },
  descricao: {
    type: DataTypes.TEXT,
    allowNull: true
  },
  data_inicio: {
    type: DataTypes.DATEONLY,
    allowNull: false
  },
  data_fim: {
    type: DataTypes.DATEONLY,
    allowNull: true // Null se for o emprego/curso atual
  },
  atual: {
    type: DataTypes.BOOLEAN,
    defaultValue: false
  }
}, {
  tableName: 'trajectories',
  timestamps: true
});

module.exports = Trajectory;