import {
    useCallback,
    useEffect,
    useLayoutEffect,
    useMemo,
    useRef,
    useState,
    type KeyboardEvent,
} from "react";
import ReactMarkdown from "react-markdown";
import {
    CHATBOT_INPUT_MAX_LEN,
    sendChatMessage,
} from "../api/chatbot";

type Role = "user" | "assistant";

interface ChatMessage {
    id: string;
    role: Role;
    content: string;
}

const SESSION_ID_KEY = "chatbot:sessionId";
const HISTORY_KEY = "chatbot:history";

interface QuickReply {
    label: string;
    message: string;
}

const QUICK_REPLIES: QuickReply[] = [
    {
        label: "Events on Lancaster Walk",
        message: "Are there any upcoming events on Lancaster Walk?",
    },
    {
        label: "Free food",
        message: "Are there any upcoming events that offer free food?",
    },
    {
        label: "Gaming events",
        message: "Tell me about upcoming gaming events.",
    },
];

function generateId(): string {
    if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
        return crypto.randomUUID().replace(/-/g, "");
    }
    return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function loadHistory(): ChatMessage[] {
    try {
        const raw = sessionStorage.getItem(HISTORY_KEY);
        if (!raw) return [];
        const parsed = JSON.parse(raw);
        if (!Array.isArray(parsed)) return [];
        return parsed.filter(
            (m): m is ChatMessage =>
                m &&
                typeof m.id === "string" &&
                (m.role === "user" || m.role === "assistant") &&
                typeof m.content === "string",
        );
    } catch {
        return [];
    }
}

function loadSessionId(): string {
    const existing = sessionStorage.getItem(SESSION_ID_KEY);
    if (existing) return existing;
    const fresh = generateId();
    sessionStorage.setItem(SESSION_ID_KEY, fresh);
    return fresh;
}

function shortenTimes(text: string): string {
    return text.replace(/(\d{1,2}):00\b/g, "$1");
}

export function ChatbotWidget() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<ChatMessage[]>(() => loadHistory());
    const [input, setInput] = useState("");
    const [isSending, setIsSending] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const sessionIdRef = useRef<string>("");
    if (!sessionIdRef.current) sessionIdRef.current = loadSessionId();

    const messagesRef = useRef<HTMLDivElement | null>(null);
    const inputRef = useRef<HTMLTextAreaElement | null>(null);
    const abortRef = useRef<AbortController | null>(null);

    useEffect(() => {
        try {
            sessionStorage.setItem(HISTORY_KEY, JSON.stringify(messages));
        } catch {
            // sessionStorage may be unavailable (private mode quota, etc.); ignore
        }
    }, [messages]);

    useLayoutEffect(() => {
        const el = messagesRef.current;
        if (el) el.scrollTop = el.scrollHeight;
    }, [messages, isOpen, isSending]);

    useEffect(() => {
        if (isOpen) {
            const id = window.setTimeout(() => inputRef.current?.focus(), 50);
            return () => window.clearTimeout(id);
        }
    }, [isOpen]);

    useEffect(() => {
        return () => abortRef.current?.abort();
    }, []);

    const trimmedInput = input.trim();
    const overLimit = trimmedInput.length > CHATBOT_INPUT_MAX_LEN;
    const canSend = trimmedInput.length > 0 && !overLimit && !isSending;

    const handleSend = useCallback(async () => {
        if (!canSend) return;
        const userMessage: ChatMessage = {
            id: generateId(),
            role: "user",
            content: trimmedInput,
        };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setError(null);
        setIsSending(true);

        const controller = new AbortController();
        abortRef.current?.abort();
        abortRef.current = controller;

        try {
            const {completion} = await sendChatMessage(
                userMessage.content,
                sessionIdRef.current,
                controller.signal,
            );
            const assistantMessage: ChatMessage = {
                id: generateId(),
                role: "assistant",
                content: completion.trim() || "(No response)",
            };
            setMessages((prev) => [...prev, assistantMessage]);
        } catch (err) {
            if ((err as { name?: string })?.name === "AbortError") return;
            console.error("[ChatbotWidget] sendChatMessage failed:", err);
            const message =
                err instanceof Error ? err.message : "Something went wrong.";
            setError(message);
        } finally {
            setIsSending(false);
        }
    }, [canSend, trimmedInput]);

    function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            void handleSend();
        }
    }

    function handleClearChat() {
        abortRef.current?.abort();
        setMessages([]);
        setError(null);
        setInput("");
        setIsSending(false);
    }

    const charCount = trimmedInput.length;
    const showCounter = charCount > CHATBOT_INPUT_MAX_LEN * 0.75;

    const placeholder = useMemo(
        () =>
            messages.length === 0
                ? "Ask about events, orgs, perks..."
                : "Type a message...",
        [messages.length],
    );

    function handleQuickReply(text: string) {
        if (isSending) return;
        const userMessage: ChatMessage = {
            id: generateId(),
            role: "user",
            content: text,
        };
        setMessages((prev) => [...prev, userMessage]);
        setError(null);
        setIsSending(true);

        const controller = new AbortController();
        abortRef.current?.abort();
        abortRef.current = controller;

        sendChatMessage(text, sessionIdRef.current, controller.signal)
            .then(({completion}) => {
                const assistantMessage: ChatMessage = {
                    id: generateId(),
                    role: "assistant",
                    content: completion.trim() || "(No response)",
                };
                setMessages((prev) => [...prev, assistantMessage]);
            })
            .catch((err) => {
                if ((err as { name?: string })?.name === "AbortError") return;
                console.error("[ChatbotWidget] sendChatMessage failed:", err);
                const message =
                    err instanceof Error ? err.message : "Something went wrong.";
                setError(message);
            })
            .finally(() => {
                setIsSending(false);
            });
    }

    return (
        <>
            <button
                type="button"
                className="chatbot-fab"
                aria-label={isOpen ? "Close chatbot" : "Open chatbot"}
                aria-expanded={isOpen}
                onClick={() => setIsOpen((v) => !v)}
            >
                {isOpen ? <CloseIcon/> : <ChatIcon/>}
            </button>

            {isOpen && (
                <div
                    className="chatbot-panel"
                    role="dialog"
                    aria-label="Event assistant chatbot"
                >
                    <header className="chatbot-panel__header">
                        <div className="chatbot-panel__title">
                            <span className="chatbot-panel__title-dot" aria-hidden="true"/>
                            <span>Event Assistant</span>
                        </div>
                        <div className="chatbot-panel__header-actions">
                            {messages.length > 0 && (
                                <button
                                    type="button"
                                    className="chatbot-panel__icon-btn"
                                    onClick={handleClearChat}
                                    aria-label="Clear conversation"
                                    title="Clear conversation"
                                >
                                    <TrashIcon/>
                                </button>
                            )}
                            <button
                                type="button"
                                className="chatbot-panel__icon-btn"
                                onClick={() => setIsOpen(false)}
                                aria-label="Close chatbot"
                                title="Close"
                            >
                                <CloseIcon/>
                            </button>
                        </div>
                    </header>

                    <div className="chatbot-panel__messages" ref={messagesRef}>
                        {messages.length === 0 && (
                            <div className="chatbot-empty">
                                <p className="chatbot-empty__title">Hi! I'm your event assistant.</p>
                                <p className="chatbot-empty__body">
                                    Ask me about upcoming Drexel events, orgs, or what's
                                    happening this week.
                                </p>
                                <div className="chatbot-quick-replies">
                                    {QUICK_REPLIES.map(({label, message}) => (
                                        <button
                                            key={label}
                                            type="button"
                                            className="chatbot-quick-reply"
                                            onClick={() => handleQuickReply(message)}
                                            disabled={isSending}
                                        >
                                            {label}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                        {messages.map((m) => (
                            <div
                                key={m.id}
                                className={
                                    "chatbot-message chatbot-message--" +
                                    (m.role === "user" ? "user" : "assistant")
                                }
                            >
                                <div className="chatbot-message__bubble">
                                    {m.role === "assistant" ? (
                                        <div className="chatbot-markdown">
                                            <ReactMarkdown
                                                components={{
                                                    a: ({href, children, ...rest}) => (
                                                        <a
                                                            {...rest}
                                                            href={href}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                        >
                                                            {children}
                                                        </a>
                                                    ),
                                                }}
                                            >
                                                {shortenTimes(m.content)}
                                            </ReactMarkdown>
                                        </div>
                                    ) : (
                                        <span>{m.content}</span>
                                    )}
                                </div>
                            </div>
                        ))}
                        {isSending && (
                            <div className="chatbot-message chatbot-message--assistant">
                                <div className="chatbot-message__bubble chatbot-message__bubble--typing">
                  <span className="chatbot-typing">
                    <span/>
                    <span/>
                    <span/>
                  </span>
                                </div>
                            </div>
                        )}
                        {error && (
                            <div className="chatbot-error" role="alert">
                                {error}
                            </div>
                        )}
                    </div>

                    <form
                        className="chatbot-panel__composer"
                        onSubmit={(e) => {
                            e.preventDefault();
                            void handleSend();
                        }}
                    >
            <textarea
                ref={inputRef}
                className="chatbot-panel__input"
                placeholder={placeholder}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                maxLength={CHATBOT_INPUT_MAX_LEN * 2}
                disabled={isSending}
            />
                        <div className="chatbot-panel__composer-footer">
              <span
                  className={
                      "chatbot-panel__counter" +
                      (overLimit ? " chatbot-panel__counter--over" : "")
                  }
                  aria-live="polite"
              >
                {showCounter || overLimit
                    ? `${charCount}/${CHATBOT_INPUT_MAX_LEN}`
                    : ""}
              </span>
                            <button
                                type="submit"
                                className="chatbot-panel__send"
                                disabled={!canSend}
                                aria-label="Send message"
                            >
                                <SendIcon/>
                            </button>
                        </div>
                    </form>
                </div>
            )}
        </>
    );
}

function ChatIcon() {
    return (
        <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            <path
                d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
        </svg>
    );
}

function CloseIcon() {
    return (
        <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
    );
}

function SendIcon() {
    return (
        <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
    );
}

function TrashIcon() {
    return (
        <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
            <path d="M10 11v6"/>
            <path d="M14 11v6"/>
            <path d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/>
        </svg>
    );
}
