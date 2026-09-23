package com.healthcompanion.ai;

import com.healthcompanion.config.AppProperties;
import java.util.Objects;
import java.util.Base64;
import java.util.Map;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import org.springframework.context.annotation.Primary;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.multipart.MultipartFile;

/** Calls the separate Python AI service when AI_MODE=production. */
@Primary
@Service
public class ProviderFoodAnalysisService implements FoodAnalysisService {
    private final AppProperties properties;
    private final MockFoodAnalysisService mock;
    private final ObjectMapper objectMapper;

    public ProviderFoodAnalysisService(AppProperties properties, MockFoodAnalysisService mock, ObjectMapper objectMapper) {
        this.properties = properties;
        this.mock = mock;
        this.objectMapper = objectMapper;
    }

    @Override
    public Result analyze(String filename, byte[] imageBytes, String contentType) {
        if ("mock".equalsIgnoreCase(properties.getAi().getMode())) {
            return mock.analyze(filename, imageBytes, contentType);
        }
        try {
            String payload = objectMapper.writeValueAsString(Map.of("filename", filename == null ? "upload" : filename,
                    "contentType", contentType,
                    "imageBase64", Base64.getEncoder().encodeToString(imageBytes)));
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(Objects.requireNonNullElse(properties.getAi().getProviderBaseUrl(), "http://localhost:8000") + "/analyze/food/base64"))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(payload))
                    .build();
            HttpResponse<String> response = HttpClient.newBuilder()
                    .version(HttpClient.Version.HTTP_1_1)
                    .build()
                    .send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() >= 300) throw new IllegalStateException("AI provider returned " + response.statusCode());
            return objectMapper.readValue(response.body(), Result.class);
        } catch (Exception exception) {
            throw new IllegalStateException("Food AI service is unavailable", exception);
        }
    }
}
