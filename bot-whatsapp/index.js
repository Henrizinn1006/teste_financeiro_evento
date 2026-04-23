const { Client } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

const client = new Client();

let usuariosAtivos = {};

client.on('qr', (qr) => {
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('Bot conectado');
});

client.on('message_create', async message => {
    const numero = message.from;
    const texto = (message.body || '').toLowerCase().trim();

    console.log("MSG:", texto);

    if (texto === 'start lion') {
        usuariosAtivos[numero] = true;
        return message.reply('🦁 Lion ativado');
    }

    if (texto === 'stop lion') {
        usuariosAtivos[numero] = false;
        return message.reply('⛔ Lion pausado');
    }

    if (!usuariosAtivos[numero]) return;

    try {
        if (message.hasMedia) {
            const media = await message.downloadMedia();

            if (media.mimetype && media.mimetype.includes('image')) {
                const resp = await axios.post(
                    'http://127.0.0.1:8000/ia/multimodal', {
                        mensagem: message.body || '',
                        imagem: media.data,
                        mime_type: media.mimetype,
                        filename: media.filename || null,
                    }
                );

                return message.reply(resp.data.resposta);
            }

            if (media.mimetype && media.mimetype.includes('audio')) {
                const resp = await axios.post(
                    'http://127.0.0.1:8000/ia/audio', {
                        audio: media.data,
                        mime_type: media.mimetype,
                        filename: media.filename || null,
                    }
                );

                const textoAudio = resp.data.texto || '';

                const resp2 = await axios.post(
                    'http://127.0.0.1:8000/ia/chat', {
                        mensagem: textoAudio,
                    }
                );

                return message.reply(resp2.data.resposta);
            }
        }

        const resp = await axios.post('http://127.0.0.1:8000/ia/chat', {
            mensagem: message.body,
        });

        message.reply(resp.data.resposta);
    } catch (err) {
        console.log(err);
        message.reply('Erro ao processar 🧠');
    }
});

client.initialize();