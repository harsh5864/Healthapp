package com.healthcompanion.ai;
public interface FoodAnalysisService {
    Result analyze(String filename, byte[] imageBytes, String contentType);
    record Result(String foodName, int freshnessScore, String condition, String observations, String recommendation) {}
}
