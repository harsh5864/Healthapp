package com.healthcompanion.ai;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.healthcompanion.config.AppProperties;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Base64;
import java.util.Map;
import java.util.Objects;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Service;

/** Calls the separate Python AI service when AI_MODE=production. */
@Primary
@Service
public class ProviderFoodAnalysisService implements FoodAnalysisService {
    private final AppProperties properties;
    private final MockFoodAnalysisService mock;
    private final ObjectMapper objectMapper;
    private final HttpClient httpClient;

    public ProviderFoodAnalysisService(AppProperties properties, MockFoodAnalysisService mock, ObjectMapper objectMapper) {
        this.properties = properties;
        this.mock = mock;
        this.objectMapper = objectMapper;
        this.httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    @Override
    public Result analyze(String filename, byte[] imageBytes, String contentType) {
        return analyze(filename, imageBytes, contentType, "PRODUCE");
    }

    @Override
    public Result analyze(String filename, byte[] imageBytes, String contentType, String scanType) {
        if ("mock".equalsIgnoreCase(properties.getAi().getMode())) {
            return mock.analyze(filename, imageBytes, contentType, scanType);
        }
        try {
            String safeScanType = (scanType == null || scanType.isBlank()) ? "PRODUCE" : scanType.trim().toUpperCase();
            String payload = objectMapper.writeValueAsString(Map.of(
                    "filename", filename == null ? "upload" : filename,
                    "contentType", contentType == null ? "image/jpeg" : contentType,
                    "imageBase64", Base64.getEncoder().encodeToString(imageBytes),
                    "scanType", safeScanType));

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(Objects.requireNonNullElse(properties.getAi().getProviderBaseUrl(), "http://localhost:8000") + "/analyze/food/base64"))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofSeconds(45))
                    .POST(HttpRequest.BodyPublishers.ofString(payload))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() >= 300) {
                throw new IllegalStateException("AI provider returned " + response.statusCode());
            }
            return objectMapper.readValue(response.body(), Result.class);
        } catch (Exception exception) {
            throw new IllegalStateException("Food AI service is unavailable", exception);
        }
    }
}
