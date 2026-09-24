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
        e.setActivity(r.resolveActivity());
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
        double mood = avg(list, 1), stress = avg(list, 2), energy = avg(list, 3), sleep = avg(list, 4), activity = avg(list, 5);
        WellnessAnalysis a = analyses.findTopByUserOrderByCreatedAtDesc(u).orElse(null);

        AnalysisResponse analysisResp = a == null ? null : AnalysisResponse.from(a, objectMapper);
        SleepLmResponse sleepLm = analysisResp != null ? analysisResp.sleepLm() : buildFallbackSleepLm(sleep, list);
        MentaResponse menta = analysisResp != null ? analysisResp.menta() : buildFallbackMenta(mood, stress, energy, activity);

        return new SummaryResponse(
                list.stream().map(EntryResponse::from).toList(),
                analysisResp,
                mood,
                stress,
                energy,
                sleep,
                activity,
                sleepLm,
                menta);
    }

    public SleepLmResponse getSleepLm(String email) {
        User u = users.current(email);
        WellnessAnalysis a = analyses.findTopByUserOrderByCreatedAtDesc(u).orElse(null);
        if (a != null && a.getSleepLmJson() != null && !a.getSleepLmJson().isBlank()) {
            try {
                return objectMapper.readValue(a.getSleepLmJson(), SleepLmResponse.class);
            } catch (Exception ignored) {}
        }
        List<WellnessEntry> list = entries.findTop30ByUserOrderByCreatedAtDesc(u);
        double sleep = avg(list, 4);
        return buildFallbackSleepLm(sleep, list);
    }

    public MentaResponse getMenta(String email) {
        User u = users.current(email);
        WellnessAnalysis a = analyses.findTopByUserOrderByCreatedAtDesc(u).orElse(null);
        if (a != null && a.getMentaJson() != null && !a.getMentaJson().isBlank()) {
            try {
                return objectMapper.readValue(a.getMentaJson(), MentaResponse.class);
            } catch (Exception ignored) {}
        }
        List<WellnessEntry> list = entries.findTop30ByUserOrderByCreatedAtDesc(u);
        double mood = avg(list, 1), stress = avg(list, 2), energy = avg(list, 3), activity = avg(list, 5);
        return buildFallbackMenta(mood, stress, energy, activity);
    }

    private double avg(List<WellnessEntry> l, int field) {
        if (l.isEmpty()) return 0;
        return Math.round(l.stream()
                .mapToDouble(e -> {
                    if (field == 1) return e.getMood();
                    if (field == 2) return e.getStress();
                    if (field == 3) return e.getEnergy();
                    if (field == 4) return e.getSleepHours();
                    return e.getActivity();
                })
                .average().orElse(0) * 10) / 10.0;
    }

    @Transactional
    public AnalysisResponse analyze(String email) {
        User u = users.current(email);
        List<WellnessEntry> l = entries.findTop30ByUserOrderByCreatedAtDesc(u);
        if (l.isEmpty()) return null;

        double mood = avg(l, 1), stress = avg(l, 2), energy = avg(l, 3), sleep = avg(l, 4), activity = avg(l, 5);

        // 1. Try AI-powered wellness pattern analysis via SleepLM & Menta in AI service
        if (!"mock".equalsIgnoreCase(properties.getAi().getMode())) {
            try {
                String baseUrl = Objects.requireNonNullElse(properties.getAi().getProviderBaseUrl(), "http://localhost:8000");
                List<Map<String, Object>> entryPayloads = l.stream().limit(7).map(e -> {
                    Map<String, Object> map = new HashMap<>();
                    map.put("mood", e.getMood());
                    map.put("stress", e.getStress());
                    map.put("energy", e.getEnergy());
                    map.put("activity", e.getActivity());
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
                        "averageActivity", activity,
                        "entries", entryPayloads);

                String json = objectMapper.writeValueAsString(requestBody);
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(baseUrl + "/wellness/analyze"))
                        .header("Content-Type", "application/json")
                        .timeout(Duration.ofSeconds(20))
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

                        if (node.has("sleepLm")) {
                            aiAnalysis.setSleepLmJson(objectMapper.writeValueAsString(node.get("sleepLm")));
                        }
                        if (node.has("menta")) {
                            aiAnalysis.setMentaJson(objectMapper.writeValueAsString(node.get("menta")));
                        }

                        return AnalysisResponse.from(analyses.save(aiAnalysis), objectMapper);
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
        a.setAnalysis("Your recent self-reported entries show mood at " + mood + "/10, stress at " + stress + "/10, activity at " + activity + "/10 and average sleep of " + sleep + " hours. These are personal trends, not a diagnosis. If changes continue or affect daily life, consider talking with someone you trust or a qualified professional.");

        SleepLmResponse sleepLm = buildFallbackSleepLm(sleep, l);
        MentaResponse menta = buildFallbackMenta(mood, stress, energy, activity);
        try {
            a.setSleepLmJson(objectMapper.writeValueAsString(sleepLm));
            a.setMentaJson(objectMapper.writeValueAsString(menta));
        } catch (Exception ignored) {}

        return AnalysisResponse.from(analyses.save(a), objectMapper);
    }

    private SleepLmResponse buildFallbackSleepLm(double avgSleep, List<WellnessEntry> list) {
        int score = avgSleep >= 7.0 && avgSleep <= 9.0 ? 88 : avgSleep >= 6.0 ? 74 : 58;
        double diff = avgSleep - 8.0;
        String debt = Math.abs(diff) < 0.5 ? "Optimal (Balanced)" : (diff > 0 ? String.format("+%.1fh (Restful)", diff) : String.format("%.1fh (Deficit)", diff));
        String consistency = list.size() > 1 ? "Moderate Consistency" : "Baseline Rhythm";
        String quality = avgSleep >= 7.5 ? "Deep & Restorative" : (avgSleep >= 6.0 ? "Adequate Recovery" : "Fragmented Rest");
        List<String> recs = List.of(
                "Keep consistent bedtime and wake anchors within 30 minutes.",
                "Dim ambient evening screens 45 minutes prior to sleep.",
                "Take 10 minutes of natural daylight exposure after waking.");
        return new SleepLmResponse(
                String.format("SleepLM analysis indicates an average sleep duration of %.1fh with %s and %s. Sleep rhythm debt status: %s.", avgSleep, consistency.toLowerCase(), quality.toLowerCase(), debt),
                score,
                debt,
                consistency,
                quality,
                recs,
                "SleepLM-Engine (Local)");
    }

    private MentaResponse buildFallbackMenta(double mood, double stress, double energy, double activity) {
        int score = (int) Math.round((mood * 3.5) + (energy * 2.5) + (activity * 2.0) + ((10.0 - stress) * 2.0));
        score = Math.max(40, Math.min(98, score));
        String moodState = mood >= 7 ? "Uplifted & Resilient" : (mood >= 5 ? "Balanced" : "Low / Fluctuating");
        String energyState = energy >= 7 ? "High Vitality" : (energy >= 5 ? "Steady" : "Depleted");
        String stressState = stress <= 4 ? "Low / Controlled" : (stress <= 7 ? "Moderate" : "Elevated");
        String activityImpact = activity >= 6.5
                ? "Physical activity is acting as an active mood elevator and stress buffer."
                : "Gentle activity levels; increasing moderate movement will raise vitality and mood resilience.";
        return new MentaResponse(
                String.format("Menta mind-body index tracks vitality at %d/100, reflecting %s and %s against %s. %s", score, moodState.toLowerCase(), energyState.toLowerCase(), stressState.toLowerCase(), activityImpact),
                score,
                moodState,
                energyState,
                stressState,
                activityImpact,
                "Practice 3 minutes of physiologic sigh breathing (2 short inhales, 1 long exhale) to re-center.",
                "Menta-Engine (Local)");
    }
}
