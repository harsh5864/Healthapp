package com.healthcompanion.ai;
import org.springframework.stereotype.Service;
@Service public class MockFoodAnalysisService implements FoodAnalysisService {
    public Result analyze(String filename, byte[] imageBytes, String contentType) {
        String name = filename != null && filename.toLowerCase().contains("banana") ? "Banana" : "Produce item";
        return new Result(name, 88, "Appears Fresh",
                "Mock mode sample: normal visible color; no image inference was performed.",
                "Wash thoroughly before eating and inspect for hidden damage or unusual odor. This image-only check cannot guarantee food safety.");
    }
}
