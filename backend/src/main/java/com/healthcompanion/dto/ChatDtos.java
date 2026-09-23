package com.healthcompanion.dto;
import com.healthcompanion.entity.*; import jakarta.validation.constraints.*; import java.time.Instant;
public final class ChatDtos {
    private ChatDtos() {}
    public record ConversationRequest(@Size(max=160) String title) {}
    public record ConversationResponse(Long id, String title, Instant createdAt, Instant updatedAt) { public static ConversationResponse from(ChatConversation c) { return new ConversationResponse(c.getId(), c.getTitle(), c.getCreatedAt(), c.getUpdatedAt()); } }
    public record MessageRequest(@NotBlank @Size(max=10000) String message) {}
    public record MessageResponse(Long id, String sender, String message, Instant timestamp) { public static MessageResponse from(ChatMessage m) { return new MessageResponse(m.getId(), m.getSender(), m.getMessage(), m.getTimestamp()); } }
}
