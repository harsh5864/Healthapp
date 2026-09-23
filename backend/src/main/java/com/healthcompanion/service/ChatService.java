package com.healthcompanion.service;

import com.healthcompanion.ai.HealthChatService;
import com.healthcompanion.dto.ChatDtos.*;
import com.healthcompanion.entity.*;
import com.healthcompanion.exception.ApiException;
import com.healthcompanion.repository.*;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ChatService {
    private static final int MAX_HISTORY_MESSAGES = 20;
    private static final int MAX_REQUESTS_PER_MINUTE = 30;

    private final ChatConversationRepository conversations;
    private final ChatMessageRepository messages;
    private final UserService users;
    private final HealthChatService ai;
    private final ConcurrentHashMap<String, Deque<Long>> rateLimits = new ConcurrentHashMap<>();

    public ChatService(ChatConversationRepository c, ChatMessageRepository m, UserService u, HealthChatService ai) {
        this.conversations = c;
        this.messages = m;
        this.users = u;
        this.ai = ai;
    }

    @Transactional
    public ConversationResponse create(String email, ConversationRequest req) {
        ChatConversation c = new ChatConversation();
        c.setUser(users.current(email));
        String title = (req != null && req.title() != null && !req.title().isBlank())
                ? req.title().trim()
                : "New Health Chat";
        c.setTitle(title);
        return ConversationResponse.from(conversations.save(c));
    }

    public List<ConversationResponse> list(String email) {
        return conversations.findByUserOrderByUpdatedAtDesc(users.current(email)).stream()
                .map(ConversationResponse::from)
                .toList();
    }

    private ChatConversation own(String email, Long id) {
        return conversations.findByIdAndUser(id, users.current(email))
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "CONVERSATION_NOT_FOUND", "Conversation not found."));
    }

    public List<MessageResponse> messages(String email, Long id) {
        return messages.findByConversationOrderByTimestampAsc(own(email, id)).stream()
                .map(MessageResponse::from)
                .toList();
    }

    private void checkRateLimit(String email) {
        long now = System.currentTimeMillis();
        long window = now - 60_000L;
        Deque<Long> timestamps = rateLimits.computeIfAbsent(email, k -> new ArrayDeque<>());
        synchronized (timestamps) {
            while (!timestamps.isEmpty() && timestamps.peekFirst() < window) {
                timestamps.pollFirst();
            }
            if (timestamps.size() >= MAX_REQUESTS_PER_MINUTE) {
                throw new ApiException(HttpStatus.TOO_MANY_REQUESTS, "RATE_LIMITED",
                        "You have sent too many messages recently. Please wait a moment before sending another.");
            }
            timestamps.addLast(now);
        }
    }

    private String generateTitle(String message) {
        if (message == null || message.isBlank()) return "Health Chat";
        String clean = message.replaceAll("[\\r\\n]+", " ").trim();
        if (clean.length() > 40) {
            clean = clean.substring(0, 37).trim() + "...";
        }
        if (!clean.isEmpty()) {
            clean = Character.toUpperCase(clean.charAt(0)) + clean.substring(1);
        }
        return clean;
    }

    @Transactional
    public List<MessageResponse> send(String email, Long id, MessageRequest req) {
        if (req == null || req.message() == null || req.message().trim().isBlank()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "INVALID_MESSAGE", "Message cannot be empty.");
        }
        String content = req.message().trim();
        if (content.length() > 10000) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "MESSAGE_TOO_LONG", "Message exceeds 10,000 characters limit.");
        }

        checkRateLimit(email);

        ChatConversation c = own(email, id);

        // Fetch existing history before adding new user message
        List<ChatMessage> existing = messages.findByConversationOrderByTimestampAsc(c);
        int start = Math.max(0, existing.size() - MAX_HISTORY_MESSAGES);
        List<MessageResponse> history = existing.subList(start, existing.size()).stream()
                .map(MessageResponse::from)
                .toList();

        // Save user message
        ChatMessage user = new ChatMessage();
        user.setConversation(c);
        user.setSender("USER");
        user.setMessage(content);
        messages.save(user);

        // Query AI assistant with context
        String aiResponse = ai.respond(content, history);

        // Save AI reply
        ChatMessage aiMsg = new ChatMessage();
        aiMsg.setConversation(c);
        aiMsg.setSender("AI");
        aiMsg.setMessage(aiResponse);
        messages.save(aiMsg);

        // Auto-update default title on first message
        if ("New health conversation".equalsIgnoreCase(c.getTitle()) || "New Health Chat".equalsIgnoreCase(c.getTitle())) {
            c.setTitle(generateTitle(content));
            conversations.save(c);
        }

        return messages.findByConversationOrderByTimestampAsc(c).stream()
                .map(MessageResponse::from)
                .toList();
    }

    @Transactional
    public void delete(String email, Long id) {
        ChatConversation c = own(email, id);
        messages.deleteByConversation(c);
        conversations.delete(c);
    }
}
