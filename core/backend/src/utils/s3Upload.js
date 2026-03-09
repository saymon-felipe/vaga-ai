const { PutObjectCommand } = require("@aws-sdk/client-s3");
const { v4: uuidv4 } = require('uuid');
const s3Client = require('../config/aws');

const uploadToS3 = async (file, folder) => {
  if (!file || !s3Client) return null;

  const ext = file.originalname.split('.').pop();
  const fileName = `${folder}/${uuidv4()}.${ext}`;
  const bucket = process.env.AWS_BUCKET;

  try {
    const command = new PutObjectCommand({
      Bucket: bucket,
      Key: fileName,
      Body: file.buffer,
      ContentType: file.mimetype
    });

    await s3Client.send(command);
    
    return `https://${bucket}.s3.${process.env.AWS_REGION || 'us-east-1'}.amazonaws.com/${fileName}`;
  } catch (error) {
    console.error("Erro no upload do S3:", error);
    return null;
  }
};

module.exports = uploadToS3;