package com.healthcompanion.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.healthcompanion.config.AppProperties;
import com.healthcompanion.dto.ChatDtos.MessageResponse;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Service;

@Primary
@Service
public class ProviderHealthChatService implements HealthChatService {

    private static final Logger log = LoggerFactory.getLogger(ProviderHealthChatService.class);

    private final AppProperties properties;
    private final MockHealthChatService mock;
    private final ObjectMapper objectMapper;
    private final HttpClient httpClient;

    public ProviderHealthChatService(AppProperties properties, MockHealthChatService mock, ObjectMapper objectMapper) {
        this.properties = properties;
        this.mock = mock;
        this.objectMapper = objectMapper;
        this.httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(5))
                .build();
    }

    @Override
    public String respond(String message) {
        return respond(message, List.of());
    }

    @Override
    public String respond(String message, List<MessageResponse> history) {
        if ("mock".equalsIgnoreCase(properties.getAi().getMode())) {
            return mock.respond(message, history);
        }

        try {
            String baseUrl = Objects.requireNonNullElse(properties.getAi().getProviderBaseUrl(), "http://localhost:8000");
            List<Map<String, String>> historyList = (history == null ? List.<MessageResponse>of() : history).stream()
                    .map(m -> Map.of("sender", m.sender() == null ? "USER" : m.sender(), "message", m.message() == null ? "" : m.message()))
                    .toList();

            Map<String, Object> payloadMap = Map.of(
                    "message", message == null ? "" : message,
                    "history", historyList
            );
            String jsonPayload = objectMapper.writeValueAsString(payloadMap);

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/chat"))
                    .header("Content-Type", "application/json")
                    .timeout(Duration.ofSeconds(15))
                    .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                JsonNode root = objectMapper.readTree(response.body());
                if (root.has("reply")) {
                    return root.get("reply").asText();
                }
            }
            log.warn("AI chat provider returned status {}, falling back to safety engine", response.statusCode());
        } catch (Exception exc) {
            log.warn("AI chat provider call failed: {}; falling back to safety engine", exc.getMessage());
        }

        // Graceful fallback to safety engine
        return mock.respond(message, history);
    }
}
