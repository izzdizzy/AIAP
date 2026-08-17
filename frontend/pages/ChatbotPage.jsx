import { useEffect, useRef, useState } from 'react';

import PrimaryButton from '../components/PrimaryButton';
import SectionCard from '../components/SectionCard';
import ChatWindow from '../components/ChatWindow';
import '../styles/chatbot.css';

import {
    createChatSession,
    sendChatMessage
} from '../services/chatService';

export default function ChatPage({
    assessmentState,
    setAssessmentState,
    chatMessages,
    setChatMessages,
    onBack
}) {
    const [status, setStatus] = useState('Preparing chat...');
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const inputRef = useRef(null);
    const messagesEndRef = useRef(null);

    const prediction = assessmentState?.prediction;

    // Prevent usage if no assessment done.
    if (!assessmentState || !prediction) {
        return (
            <div className="page-stack">
                <SectionCard
                    title="AI Health Chatbot"
                    description="No assessment found."
                >
                    <p>
                        Please complete a CAD risk assessment before using the AI
                        chatbot.
                    </p>

                    <div className="form-actions">
                        <PrimaryButton onClick={onBack}>
                            Back
                        </PrimaryButton>
                    </div>
                </SectionCard>
            </div>
        );
    }

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({
            behavior: 'smooth'
        });
    }, [chatMessages, loading]);

    useEffect(() => {
        async function initializeChat() {
            if (!assessmentState) {
                setStatus('No assessment found.');
                return;
            }

            // Create greeting only once
            if (chatMessages.length === 0) {
                setChatMessages([
                    {
                        role: 'assistant',
                        content:
                            `# Welcome!

I've reviewed your CAD screening assessment.

**Risk Level:** ${prediction.riskLevel}

**Estimated Risk:** ${prediction.riskPercent}

You can ask me about:

- Your assessment results
- Medical terminology
- Lifestyle recommendations
- Coronary artery disease (CAD)

How can I help you today?`
                    }
                ]);
            }

            // Existing session
            if (assessmentState.sessionId) {
                setStatus('Chat ready.');
                return;
            }

            try {
                const sessionId = await createChatSession(
                    assessmentState.assessment,
                    prediction.backendPrediction
                );

                setAssessmentState(previous => ({
                    ...previous,
                    sessionId
                }));

                setStatus('Chat ready.');
            } catch (error) {
                console.error(error);
                setStatus('Unable to start chat.');
            }
        }

        initializeChat();
        inputRef.current?.focus();
    }, [assessmentState?.sessionId]);

    async function handleSend() {
        const message = input.trim();

        if (!message || loading) {
            return;
        }

        setChatMessages(previous => [
            ...previous,
            {
                role: 'user',
                content: message
            }
        ]);

        setInput('');
        setLoading(true);

        try {
            const reply = await sendChatMessage(
                assessmentState.sessionId,
                message
            );

            setChatMessages(previous => [
                ...previous,
                {
                    role: 'assistant',
                    content: reply
                }
            ]);
        } catch (error) {
            console.error(error);

            setChatMessages(previous => [
                ...previous,
                {
                    role: 'assistant',
                    content:
                        'Sorry, something went wrong while contacting the AI assistant.'
                }
            ]);
        } finally {
            setLoading(false);
        }
    }

    function handleNewChat() {
        setAssessmentState(previous => {
            if (!previous) {
                return previous;
            }

            return {
                ...previous,
                sessionId: null,
                chatMessages: []
            };
        });

        setStatus('Preparing chat...');
    }

    function handleKeyDown(event) {
        if (
            event.key === 'Enter' &&
            !event.shiftKey &&
            !loading
        ) {
            event.preventDefault();
            handleSend();
        }
    }

    return (
        <div className="page-stack">

            <SectionCard
                title="AI Health Chatbot"
                description={status}
            >

                <div className="chat-summary">

                    <div>
                        <span className="results-summary__label">
                            Risk Level
                        </span>

                        <strong>
                            {prediction.riskLevel}
                        </strong>
                    </div>

                    <div>
                        <span className="results-summary__label">
                            Estimated Risk
                        </span>

                        <strong>
                            {prediction.riskPercent}
                        </strong>
                    </div>

                </div>

                <ChatWindow
                    messages={chatMessages}
                    loading={loading}
                    messagesEndRef={messagesEndRef}
                />

                <textarea
                    className="chat-input"
                    rows={3}
                    placeholder="Ask about your assessment or heart health..."
                    value={input}
                    onChange={(event) => setInput(event.target.value)}
                    onKeyDown={handleKeyDown}
                    ref={inputRef}
                />

                <div className="form-actions">

                    <PrimaryButton
                        variant="ghost"
                        onClick={onBack}
                        disabled={loading}
                    >
                        Back
                    </PrimaryButton>

                    <PrimaryButton
                        variant="ghost"
                        onClick={handleNewChat}
                        disabled={loading}
                    >
                        New Chat
                    </PrimaryButton>
                    
                    <PrimaryButton
                        onClick={handleSend}
                        disabled={loading || !input.trim()}
                    >
                        {loading ? 'Thinking...' : 'Send'}
                    </PrimaryButton>

                </div>

            </SectionCard>

        </div>
    );
}