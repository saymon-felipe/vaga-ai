const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Profile = sequelize.define('Profile', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  nome: {
    type: DataTypes.STRING,
    allowNull: false
  },
  email: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: 'uk_profile_email_fixo'
  },
  telefone: {
    type: DataTypes.STRING
  },
  nivel: {
    type: DataTypes.STRING
  },
  foto_url: {
    type: DataTypes.TEXT
  },
  curriculo_url: {
    type: DataTypes.TEXT
  }
}, {
  tableName: 'profiles',
  timestamps: false
});

module.exports = Profile;