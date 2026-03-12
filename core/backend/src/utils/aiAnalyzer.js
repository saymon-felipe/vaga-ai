const { OpenAI } = require('openai');

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const analyzeBehavioralProfile = async (answers) => {
  const prompt = `
    Atue como um psicólogo organizacional sênior.
    Analise as seguintes respostas de um questionário comportamental de um profissional:
    ${JSON.stringify(answers)}

    Retorne APENAS um objeto JSON válido, sem formatação markdown, com a seguinte estrutura exata:
    {
      "arquétipo": "Nome curto do perfil (ex: Estrategista Analítico)",
      "resumo": "Parágrafo resumindo o perfil profissional",
      "big_five": {
        "abertura": 0-100,
        "conscienciosidade": 0-100,
        "extroversao": 0-100,
        "amabilidade": 0-100,
        "neuroticismo": 0-100
      },
      "disc": {
        "dominancia": 0-100,
        "influencia": 0-100,
        "estabilidade": 0-100,
        "conformidade": 0-100
      },
      "inteligencias_principais": ["Inteligência 1", "Inteligência 2"],
      "pontos_fortes": ["Ponto 1", "Ponto 2", "Ponto 3"],
      "pontos_desenvolvimento": ["Ponto 1", "Ponto 2"]
    }
  `;

  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4.1-nano',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.2,
      response_format: { type: 'json_object' }
    });

    return JSON.parse(response.choices[0].message.content);
  } catch (error) {
    console.error('Erro na análise da IA:', error);
    throw new Error('Falha ao processar perfil com a IA');
  }
};

module.exports = { analyzeBehavioralProfile };