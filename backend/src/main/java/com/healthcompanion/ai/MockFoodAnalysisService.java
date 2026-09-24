package com.healthcompanion.ai;

import org.springframework.stereotype.Service;

@Service
public class MockFoodAnalysisService implements FoodAnalysisService {

    @Override
    public Result analyze(String filename, byte[] imageBytes, String contentType) {
        return analyze(filename, imageBytes, contentType, "PRODUCE");
    }

    @Override
    public Result analyze(String filename, byte[] imageBytes, String contentType, String scanType) {
        if ("REAL_FOOD".equalsIgnoreCase(scanType)) {
            return new Result(
                    "Mediterranean Quinoa & Grilled Chicken Bowl (Mock)",
                    92,
                    "Nutrient-Dense Balanced Meal",
                    "Mock mode sample: rich in lean protein, complex carbs, and dietary fiber.",
                    "Excellent post-workout or wholesome dinner choice.",
                    null,
                    "REAL_FOOD",
                    480,
                    35.0,
                    46.0,
                    14.0,
                    7.0,
                    "1 standard bowl (~380g)");
        }
        if ("PACKED_FOOD".equalsIgnoreCase(scanType)) {
            return new Result(
                    "Oatmeal & Granola Bar (Mock)",
                    90,
                    "Grade A - Excellent Choice",
                    "Mock mode sample: clean whole food ingredient profile, zero artificial additives.",
                    "Great whole grain breakfast or on-the-go snack.",
                    "A",
                    "PACKED_FOOD");
        }
        String name = filename != null && filename.toLowerCase().contains("banana") ? "Banana" : "Produce item";
        return new Result(
                name,
                88,
                "Appears Fresh",
                "Mock mode sample: normal visible color; no image inference was performed.",
                "Wash thoroughly before eating and inspect for hidden damage or unusual odor. This image-only check cannot guarantee food safety.",
                null,
                "PRODUCE");
    }
}
