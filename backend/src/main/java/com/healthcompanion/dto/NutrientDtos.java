package com.healthcompanion.dto;

import com.healthcompanion.entity.NutrientIntake;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.Instant;
import java.time.LocalDate;
import java.util.List;

public final class NutrientDtos {
    private NutrientDtos() {}

    public record LogIntakeRequest(
        @NotBlank(message = "Food name is required")
        String foodName,
        String mealType,
        @NotNull(message = "Calories is required")
        Integer calories,
        Double protein,
        Double carbs,
        Double fat,
        Double fiber,
        String portionSize,
        String notes,
        LocalDate intakeDate
    ) {}

    public record IntakeItemResponse(
        Long id,
        String foodName,
        String mealType,
        Integer calories,
        Double protein,
        Double carbs,
        Double fat,
        Double fiber,
        String portionSize,
        String notes,
        LocalDate intakeDate,
        Instant createdAt
    ) {
        public static IntakeItemResponse from(NutrientIntake entity) {
            return new IntakeItemResponse(
                entity.getId(),
                entity.getFoodName(),
                entity.getMealType(),
                entity.getCalories(),
                entity.getProtein(),
                entity.getCarbs(),
                entity.getFat(),
                entity.getFiber(),
                entity.getPortionSize(),
                entity.getNotes(),
                entity.getIntakeDate(),
                entity.getCreatedAt()
            );
        }
    }

    public record DaySummaryDto(
        LocalDate date,
        String label,
        int totalCalories,
        double totalProtein,
        double totalCarbs,
        double totalFat,
        double totalFiber,
        List<IntakeItemResponse> items
    ) {}

    public record ThreeDayOverviewDto(
        DaySummaryDto today,
        List<DaySummaryDto> history,
        int dailyCalorieTarget,
        double dailyProteinTarget,
        double dailyCarbsTarget,
        double dailyFatTarget,
        double dailyFiberTarget
    ) {}
}
