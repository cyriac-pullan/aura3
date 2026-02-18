
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(express.json());

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: false, // Show browser for better debugging and stability
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

let isReady = false;

client.on('qr', (qr) => {
    console.log('QR RECEIVED', qr);
    qrcode.generate(qr, { small: true });
    console.log('Please scan the QR code with your phone.');
});

client.on('ready', () => {
    console.log('WhatsApp Client is ready!');
    isReady = true;
});

client.on('authenticated', () => {
    console.log('AUTHENTICATED');
});

client.on('auth_failure', msg => {
    console.error('AUTHENTICATION FAILURE', msg);
});

client.initialize();

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'ok', ready: isReady });
});

// API Endpoint to send text message
app.post('/send-message', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: 'Client not ready. Please scan QR code.' });
    }

    const { contact, message } = req.body;

    try {
        const chats = await client.getChats();
        const targetChat = chats.find(c => c.name === contact || (c.id.user === contact));

        if (!targetChat) {
            return res.status(404).json({ error: `Contact '${contact}' not found.` });
        }

        await client.sendMessage(targetChat.id._serialized, message);
        res.json({ status: 'success', message: 'Message sent!' });
    } catch (error) {
        console.error('Error sending message:', error);
        res.status(500).json({ error: error.message });
    }
});

// API Endpoint to send file
app.post('/send-file', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: 'Client not ready. Please scan QR code.' });
    }

    const { contact, filePath, caption } = req.body;

    if (!fs.existsSync(filePath)) {
        return res.status(400).json({ error: `File not found: ${filePath}` });
    }

    try {
        const chats = await client.getChats();
        const targetChat = chats.find(c => c.name === contact || (c.id.user === contact));

        if (!targetChat) {
            return res.status(404).json({ error: `Contact '${contact}' not found.` });
        }

        const media = MessageMedia.fromFilePath(filePath);
        await client.sendMessage(targetChat.id._serialized, media, { caption: caption });

        res.json({ status: 'success', message: 'File sent!' });
    } catch (error) {
        console.error('Error sending file:', error);
        res.status(500).json({ error: error.message });
    }
});

// API Endpoint to get unread messages
app.get('/unread-messages', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: 'Client not ready. Please scan QR code.' });
    }

    try {
        const chats = await client.getChats();
        const unreadChats = [];

        for (const chat of chats) {
            if (chat.unreadCount > 0) {
                // Fetch recent unread messages
                const messages = await chat.fetchMessages({ limit: chat.unreadCount > 10 ? 10 : chat.unreadCount });
                const recentMessages = messages.map(msg => ({
                    from: msg.from,
                    fromName: msg._data.notifyName || msg.from,
                    body: msg.body,
                    timestamp: msg.timestamp,
                    time: new Date(msg.timestamp * 1000).toLocaleString(),
                    hasMedia: msg.hasMedia,
                    type: msg.type
                }));

                unreadChats.push({
                    name: chat.name,
                    isGroup: chat.isGroup,
                    unreadCount: chat.unreadCount,
                    messages: recentMessages
                });
            }
        }

        res.json({
            status: 'success',
            totalUnread: unreadChats.reduce((sum, c) => sum + c.unreadCount, 0),
            chats: unreadChats
        });
    } catch (error) {
        console.error('Error fetching unread messages:', error);
        res.status(500).json({ error: error.message });
    }
});

// API Endpoint to get contacts/chats list
app.get('/contacts', async (req, res) => {
    if (!isReady) {
        return res.status(503).json({ error: 'Client not ready. Please scan QR code.' });
    }

    try {
        const chats = await client.getChats();
        const limit = parseInt(req.query.limit) || 50;

        const contactList = chats.slice(0, limit).map(chat => ({
            name: chat.name,
            isGroup: chat.isGroup,
            unreadCount: chat.unreadCount,
            lastMessage: chat.lastMessage ? {
                body: chat.lastMessage.body ? chat.lastMessage.body.substring(0, 100) : '',
                timestamp: chat.lastMessage.timestamp,
                time: chat.lastMessage.timestamp
                    ? new Date(chat.lastMessage.timestamp * 1000).toLocaleString()
                    : ''
            } : null
        }));

        res.json({
            status: 'success',
            total: contactList.length,
            contacts: contactList
        });
    } catch (error) {
        console.error('Error fetching contacts:', error);
        res.status(500).json({ error: error.message });
    }
});

const PORT = 3000;
app.listen(PORT, () => {
    console.log(`WhatsApp Bot Service running on port ${PORT}`);
});
