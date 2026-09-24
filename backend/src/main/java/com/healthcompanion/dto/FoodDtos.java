package com.healthcompanion.dto;
import com.healthcompanion.entity.FoodScan; import java.time.Instant;
public final class FoodDtos {
    private FoodDtos() {}
    public record FoodResponse(
        Long id, 
        String imageUrl, 
        String foodName, 
        Integer freshnessScore, 
        String condition, 
        String observations, 
        String recommendation, 
        Instant createdAt, 
        boolean mock, 
        String scanType, 
        String grade,
        Integer calories,
        Double protein,
        Double carbs,
        Double fat,
        Double fiber,
        String portionSize
    ) {
        public static FoodResponse from(FoodScan scan, boolean mock) {
            return new FoodResponse(
                scan.getId(), 
                scan.getImageUrl(), 
                scan.getFoodName(), 
                scan.getFreshnessScore(), 
                scan.getCondition(), 
                scan.getObservations(), 
                scan.getRecommendation(), 
                scan.getCreatedAt(), 
                mock, 
                scan.getScanType(), 
                scan.getGrade(),
                scan.getCalories(),
                scan.getProtein(),
                scan.getCarbs(),
                scan.getFat(),
                scan.getFiber(),
                scan.getPortionSize()
            );
        }
    }
}
