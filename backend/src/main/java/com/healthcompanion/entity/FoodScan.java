package com.healthcompanion.entity;

import jakarta.persistence.*;
import java.time.Instant;

@Entity @Table(name = "food_scans")
public class FoodScan {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @ManyToOne(fetch = FetchType.LAZY, optional = false) @JoinColumn(name = "user_id", nullable = false) private User user;
    @Column(nullable = false) private String imageUrl;
    @Column(nullable = false, length = 80) private String foodName;
    @Column(nullable = false) private Integer freshnessScore;
    // `condition` is reserved by MySQL; keep the API property name while using a safe column name.
    @Column(name = "food_condition", nullable = false, length = 50) private String condition;
    @Column(nullable = false, columnDefinition = "TEXT") private String observations;
    @Column(nullable = false, columnDefinition = "TEXT") private String recommendation;
    @Column(name = "scan_type", length = 30) private String scanType = "PRODUCE";
    @Column(name = "grade", length = 10) private String grade;
    @Column(name = "calories") private Integer calories;
    @Column(name = "protein") private Double protein;
    @Column(name = "carbs") private Double carbs;
    @Column(name = "fat") private Double fat;
    @Column(name = "fiber") private Double fiber;
    @Column(name = "portion_size", length = 100) private String portionSize;
    @Column(nullable = false, updatable = false) private Instant createdAt;
    @PrePersist void onCreate() { createdAt = Instant.now(); }
    public Long getId() { return id; }
    public User getUser() { return user; } public void setUser(User user) { this.user = user; }
    public String getImageUrl() { return imageUrl; } public void setImageUrl(String v) { imageUrl = v; }
    public String getFoodName() { return foodName; } public void setFoodName(String v) { foodName = v; }
    public Integer getFreshnessScore() { return freshnessScore; } public void setFreshnessScore(Integer v) { freshnessScore = v; }
    public String getCondition() { return condition; } public void setCondition(String v) { condition = v; }
    public String getObservations() { return observations; } public void setObservations(String v) { observations = v; }
    public String getRecommendation() { return recommendation; } public void setRecommendation(String v) { recommendation = v; }
    public String getScanType() { return scanType; } public void setScanType(String v) { scanType = v; }
    public String getGrade() { return grade; } public void setGrade(String v) { grade = v; }
    public Integer getCalories() { return calories; } public void setCalories(Integer v) { calories = v; }
    public Double getProtein() { return protein; } public void setProtein(Double v) { protein = v; }
    public Double getCarbs() { return carbs; } public void setCarbs(Double v) { carbs = v; }
    public Double getFat() { return fat; } public void setFat(Double v) { fat = v; }
    public Double getFiber() { return fiber; } public void setFiber(Double v) { fiber = v; }
    public String getPortionSize() { return portionSize; } public void setPortionSize(String v) { portionSize = v; }
    public Instant getCreatedAt() { return createdAt; }
}
