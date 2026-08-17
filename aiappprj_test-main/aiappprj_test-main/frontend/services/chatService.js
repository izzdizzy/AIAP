const DEFAULT_API_BASE_URL = 'http://localhost:8000';

const apiBaseUrl =
    import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;

/**
 * Creates a new chatbot session using the completed assessment.
 */
export async function createChatSession(assessment, prediction) {
    const response = await fetch(`${apiBaseUrl}/api/chat/session`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            assessment,
            prediction
        })
    });

    if (!response.ok) {
        throw new Error(`Chat session request failed (${response.status})`);
    }

    const data = await response.json();

    return data.session_id;
}

/**
 * Sends a user message to the chatbot.
 */
export async function sendChatMessage(sessionId, message) {
    console.log('Sending sessionId:', sessionId);

    const response = await fetch(`${apiBaseUrl}/api/chat/message`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: sessionId,
            message
        })
    });

    if (!response.ok) {
        throw new Error(`Chat request failed (${response.status})`);
    }

    const data = await response.json();

    return data.reply;
}