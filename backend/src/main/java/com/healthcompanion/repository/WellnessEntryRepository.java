package com.healthcompanion.repository;
import com.healthcompanion.entity.*; import java.util.*; import org.springframework.data.jpa.repository.JpaRepository;
public interface WellnessEntryRepository extends JpaRepository<WellnessEntry, Long> { List<WellnessEntry> findTop30ByUserOrderByCreatedAtDesc(User user); long countByUser(User user); }
