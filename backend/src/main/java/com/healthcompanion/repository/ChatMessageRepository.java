package com.healthcompanion.repository;
import com.healthcompanion.entity.*; import java.util.*; import org.springframework.data.jpa.repository.JpaRepository;
public interface ChatMessageRepository extends JpaRepository<ChatMessage, Long> {
    List<ChatMessage> findByConversationOrderByTimestampAsc(ChatConversation conversation);
    void deleteByConversation(ChatConversation conversation);
}
