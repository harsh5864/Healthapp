package com.healthcompanion.repository;

import com.healthcompanion.entity.NutrientIntake;
import com.healthcompanion.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface NutrientIntakeRepository extends JpaRepository<NutrientIntake, Long> {
    List<NutrientIntake> findByUserAndIntakeDateGreaterThanEqualOrderByCreatedAtDesc(User user, LocalDate startDate);
    List<NutrientIntake> findByUserAndIntakeDateOrderByCreatedAtDesc(User user, LocalDate date);
    Optional<NutrientIntake> findByIdAndUser(Long id, User user);

    @Modifying
    @Transactional
    void deleteByUserAndIntakeDateBefore(User user, LocalDate cutoffDate);
}
