package com.healthcompanion.repository;
import com.healthcompanion.entity.*; import java.util.*; import org.springframework.data.jpa.repository.JpaRepository;
public interface FoodScanRepository extends JpaRepository<FoodScan, Long> { List<FoodScan> findTop20ByUserOrderByCreatedAtDesc(User user); Optional<FoodScan> findByIdAndUser(Long id, User user); long countByUser(User user); }
