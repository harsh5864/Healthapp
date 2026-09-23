package com.healthcompanion.repository;
import com.healthcompanion.entity.*; import java.util.*; import org.springframework.data.jpa.repository.JpaRepository;
public interface WellnessAnalysisRepository extends JpaRepository<WellnessAnalysis, Long> { Optional<WellnessAnalysis> findTopByUserOrderByCreatedAtDesc(User user); }
