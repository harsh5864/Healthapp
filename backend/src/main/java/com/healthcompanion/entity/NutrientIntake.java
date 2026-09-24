package com.healthcompanion.entity;

import jakarta.persistence.*;
import java.time.Instant;
import java.time.LocalDate;

@Entity
@Table(name = "nutrient_intakes")
public class NutrientIntake {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(nullable = false, length = 100)
    private String foodName;

    @Column(nullable = false, length = 30)
    private String mealType = "LUNCH";

    @Column(nullable = false)
    private Integer calories = 0;

    @Column(nullable = false)
    private Double protein = 0.0;

    @Column(nullable = false)
    private Double carbs = 0.0;

    @Column(nullable = false)
    private Double fat = 0.0;

    @Column(nullable = false)
    private Double fiber = 0.0;

    @Column(length = 100)
    private String portionSize;

    @Column(columnDefinition = "TEXT")
    private String notes;

    @Column(nullable = false)
    private LocalDate intakeDate;

    @Column(nullable = false, updatable = false)
    private Instant createdAt;

    @PrePersist
    void onCreate() {
        if (createdAt == null) createdAt = Instant.now();
        if (intakeDate == null) intakeDate = LocalDate.now();
    }

    public Long getId() { return id; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
    public String getFoodName() { return foodName; }
    public void setFoodName(String foodName) { this.foodName = foodName; }
    public String getMealType() { return mealType; }
    public void setMealType(String mealType) { this.mealType = mealType; }
    public Integer getCalories() { return calories; }
    public void setCalories(Integer calories) { this.calories = calories; }
    public Double getProtein() { return protein; }
    public void setProtein(Double protein) { this.protein = protein; }
    public Double getCarbs() { return carbs; }
    public void setCarbs(Double carbs) { this.carbs = carbs; }
    public Double getFat() { return fat; }
    public void setFat(Double fat) { this.fat = fat; }
    public Double getFiber() { return fiber; }
    public void setFiber(Double fiber) { this.fiber = fiber; }
    public String getPortionSize() { return portionSize; }
    public void setPortionSize(String portionSize) { this.portionSize = portionSize; }
    public String getNotes() { return notes; }
    public void setNotes(String notes) { this.notes = notes; }
    public LocalDate getIntakeDate() { return intakeDate; }
    public void setIntakeDate(LocalDate intakeDate) { this.intakeDate = intakeDate; }
    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
