package com.healthcompanion.entity;

import jakarta.persistence.*;
import java.time.Instant;

@Entity @Table(name = "chat_messages")
public class ChatMessage {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @ManyToOne(fetch = FetchType.LAZY, optional = false) @JoinColumn(name = "conversation_id", nullable = false) private ChatConversation conversation;
    @Column(nullable = false, length = 20) private String sender;
    @Column(nullable = false, columnDefinition = "TEXT") private String message;
    @Column(nullable = false, updatable = false) private Instant timestamp;
    @PrePersist void onCreate() { timestamp = Instant.now(); }
    public Long getId() { return id; } public ChatConversation getConversation() { return conversation; } public void setConversation(ChatConversation v) { conversation = v; }
    public String getSender() { return sender; } public void setSender(String v) { sender = v; }
    public String getMessage() { return message; } public void setMessage(String v) { message = v; }
    public Instant getTimestamp() { return timestamp; }
}
