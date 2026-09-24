package com.healthcompanion.ai;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

public interface FoodAnalysisService {
    Result analyze(String filename, byte[] imageBytes, String contentType);
    Result analyze(String filename, byte[] imageBytes, String contentType, String scanType);

    @JsonIgnoreProperties(ignoreUnknown = true)
    record Result(
        String foodName,
        int freshnessScore,
        String condition,
        String observations,
        String recommendation,
        String grade,
        String scanType,
        Integer calories,
        Double protein,
        Double carbs,
        Double fat,
        Double fiber,
        String portionSize
    ) {
        public Result(String foodName, int freshnessScore, String condition, String observations, String recommendation) {
            this(foodName, freshnessScore, condition, observations, recommendation, null, "PRODUCE", null, null, null, null, null, null);
        }

        public Result(String foodName, int freshnessScore, String condition, String observations, String recommendation, String grade, String scanType) {
            this(foodName, freshnessScore, condition, observations, recommendation, grade, scanType, null, null, null, null, null, null);
        }
    }
}
