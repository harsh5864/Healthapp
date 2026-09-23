package com.healthcompanion.repository;
import com.healthcompanion.entity.*; import java.util.*; import org.springframework.data.jpa.repository.JpaRepository;
public interface ChatConversationRepository extends JpaRepository<ChatConversation, Long> { List<ChatConversation> findByUserOrderByUpdatedAtDesc(User user); Optional<ChatConversation> findByIdAndUser(Long id, User user); long countByUser(User user); }
