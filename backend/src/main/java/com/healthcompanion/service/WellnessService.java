package com.healthcompanion.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.healthcompanion.config.AppProperties;
import com.healthcompanion.dto.WellnessDtos.*;
import com.healthcompanion.entity.*;
import com.healthcompanion.repository.*;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class WellnessService {
    private static final Logger log = LoggerFactory.getLogger(WellnessService.class);

    private final WellnessEntryRepository entries;
    private final WellnessAnalysisRepository analyses;
    private final UserService users;
    private final AppProperties properties;
    private final ObjectMapper objectMapper;
    private final HttpClient httpClient;

    public WellnessService(
            WellnessEntryRepository entries,
            WellnessAnalysisRepository analyses,
            UserService users,
            AppProperties properties,
            ObjectMapper objectMapper) {
        this.entries = entries;
        this.analyses = analyses;
        this.users = users;
        this.properties = properties;
        this.objectMapper = objectMapper;
        this.httpClient = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(5))
                .build();
    }

    @Transactional
    public SummaryResponse checkIn(String email, CheckInRequest r) {
        User u = users.current(email);
        WellnessEntry e = new WellnessEntry();
        e.setUser(u);
        e.setMood(r.mood());
        e.setStress(r.stress());
        e.setEnergy(r.energy());
        e.setSleepHours(r.sleepHours());
        e.setJournalText(r.journalText());
        entries.save(e);

        // Auto-refresh analysis with fresh input
        try {
            analyze(email);
        } catch (Exception ex) {
            log.warn("Automatic wellness analysis on check-in skipped: {}", ex.getMessage());
        }

        return summary(email);
    }

    public List<EntryResponse> history(String email) {
        return entries.findTop30ByUserOrderByCreatedAtDesc(users.current(email)).stream()
                .map(EntryResponse::from)
                .toList();
    }

    public SummaryResponse summary(String email) {
        User u = users.current(email);
        List<WellnessEntry> list = entries.findTop30ByUserOrderByCreatedAtDesc(u);
        double mood = avg(list, 1), stress = avg(list, 2), energy = avg(list, 3), sleep = avg(list, 4);
        WellnessAnalysis a = analyses.findTopByUserOrderByCreatedAtDesc(u).orElse(null);
        return new SummaryResponse(
                list.stream().map(EntryResponse::from).toList(),
                a == null ? null : AnalysisResponse.from(a),
                mood,
                stress,
                energy,
                sleep);
    }

    private double avg(List<WellnessEntry> l, int field) {
        if (l.isEmpty()) return 0;
        return Math.round(l.stream()
                .mapToDouble(e -> field == 1 ? e.getMood() : field == 2 ? e.getStress() : field == 3 ? e.getEnergy() : e.getSleepHours())
                .average().orElse(0) * 10) / 10.0;
    }

    @Transactional
    public AnalysisResponse analyze(String email) {
        User u = users.current(email);
        List<WellnessEntry> l = entries.findTop30ByUserOrderByCreatedAtDesc(u);
        if (l.isEmpty()) return null;

        double mood = avg(l, 1), stress = avg(l, 2), energy = avg(l, 3), sleep = avg(l, 4);

        // 1. Try AI-powered wellness pattern analysis via OpenRouter
        if (!"mock".equalsIgnoreCase(properties.getAi().getMode())) {
            try {
                String baseUrl = Objects.requireNonNullElse(properties.getAi().getProviderBaseUrl(), "http://localhost:8000");
                List<Map<String, Object>> entryPayloads = l.stream().limit(5).map(e -> {
                    Map<String, Object> map = new HashMap<>();
                    map.put("mood", e.getMood());
                    map.put("stress", e.getStress());
                    map.put("energy", e.getEnergy());
                    map.put("sleepHours", e.getSleepHours());
                    map.put("journalText", e.getJournalText() == null ? "" : e.getJournalText());
                    map.put("createdAt", e.getCreatedAt() == null ? "" : e.getCreatedAt().toString());
                    return map;
                }).toList();

                Map<String, Object> requestBody = Map.of(
                        "averageMood", mood,
                        "averageStress", stress,
                        "averageEnergy", energy,
                        "averageSleep", sleep,
                        "entries", entryPayloads);

                String json = objectMapper.writeValueAsString(requestBody);
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(baseUrl + "/wellness/analyze"))
                        .header("Content-Type", "application/json")
                        .timeout(Duration.ofSeconds(15))
                        .POST(HttpRequest.BodyPublishers.ofString(json))
                        .build();

                HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
                if (response.statusCode() >= 200 && response.statusCode() < 300) {
                    JsonNode node = objectMapper.readTree(response.body());
                    if (node.has("analysis") && node.has("moodTrend")) {
                        WellnessAnalysis aiAnalysis = new WellnessAnalysis();
                        aiAnalysis.setUser(u);
                        aiAnalysis.setMoodTrend(node.get("moodTrend").asText("Stable / positive"));
                        aiAnalysis.setStressTrend(node.get("stressTrend").asText("Manageable"));
                        aiAnalysis.setSleepTrend(node.get("sleepTrend").asText("Steady"));
                        aiAnalysis.setAnalysis(node.get("analysis").asText());
                        return AnalysisResponse.from(analyses.save(aiAnalysis));
                    }
                }
                log.warn("AI wellness service returned status {}, falling back to local engine", response.statusCode());
            } catch (Exception exc) {
                log.warn("AI wellness analysis failed: {}; falling back to local engine", exc.getMessage());
            }
        }

        // 2. Rule-based fallback
        WellnessAnalysis a = new WellnessAnalysis();
        a.setUser(u);
        a.setMoodTrend(mood >= 6 ? "Stable / positive" : "Lower recently");
        a.setStressTrend(stress <= 4 ? "Lower recently" : "Higher recently");
        a.setSleepTrend(sleep >= 7 ? "Steady" : "Slightly reduced");
        a.setAnalysis("Your recent self-reported entries show mood at " + mood + "/10, stress at " + stress + "/10 and average sleep of " + sleep + " hours. These are personal trends, not a diagnosis. If changes continue or affect daily life, consider talking with someone you trust or a qualified professional.");
        return AnalysisResponse.from(analyses.save(a));
    }
}
