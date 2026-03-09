const { S3Client } = require("@aws-sdk/client-s3");
require('dotenv').config();

let s3Client = null;

if (process.env.AWS_ACCESS_KEY && process.env.AWS_SECRET_KEY) {
  s3Client = new S3Client({
    region: process.env.AWS_REGION || "us-east-1",
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY,
      secretAccessKey: process.env.AWS_SECRET_KEY
    }
  });
}

module.exports = s3Client;