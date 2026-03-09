const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const BehavioralProfile = sequelize.define('BehavioralProfile', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  raw_answers: {
    type: DataTypes.JSON,
    allowNull: false
  },
  ai_analysis: {
    type: DataTypes.JSON,
    allowNull: false
  }
}, {
  tableName: 'behavioral_profiles',
  timestamps: true
});

module.exports = BehavioralProfile;