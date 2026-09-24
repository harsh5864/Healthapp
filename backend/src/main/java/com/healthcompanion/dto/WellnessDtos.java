package com.healthcompanion.dto;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.healthcompanion.entity.*;
import jakarta.validation.constraints.*;
import java.time.Instant;
import java.util.*;

public final class WellnessDtos {
    private WellnessDtos() {}

    public record CheckInRequest(
            @NotNull @Min(1) @Max(10) Integer mood,
            @NotNull @Min(1) @Max(10) Integer stress,
            @NotNull @Min(1) @Max(10) Integer energy,
            @NotNull @DecimalMin("0") @DecimalMax("24") Double sleepHours,
            @Min(1) @Max(10) Integer activity,
            @Size(max=5000) String journalText) {
        public Integer resolveActivity() {
            return activity != null ? activity : 5;
        }
    }

    public record EntryResponse(
            Long id,
            Integer mood,
            Integer stress,
            Integer energy,
            Double sleepHours,
            Integer activity,
            String journalText,
            Instant createdAt) {
        public static EntryResponse from(WellnessEntry e) {
            return new EntryResponse(
                    e.getId(),
                    e.getMood(),
                    e.getStress(),
                    e.getEnergy(),
                    e.getSleepHours(),
                    e.getActivity(),
                    e.getJournalText(),
                    e.getCreatedAt());
        }
    }

    public record SleepLmResponse(
            String sleepSummary,
            Integer sleepScore,
            String sleepDebt,
            String sleepConsistency,
            String restorativeQuality,
            List<String> recommendations,
            String provider) {}

    public record MentaResponse(
            String mentaSummary,
            Integer wellnessScore,
            String moodState,
            String energyLevel,
            String stressLevel,
            String activityImpact,
            String mindfulnessAction,
            String provider) {}

    public record AnalysisResponse(
            String analysis,
            String moodTrend,
            String stressTrend,
            String sleepTrend,
            SleepLmResponse sleepLm,
            MentaResponse menta,
            Instant createdAt) {
        public static AnalysisResponse from(WellnessAnalysis a, ObjectMapper mapper) {
            SleepLmResponse sleepLm = null;
            MentaResponse menta = null;
            if (mapper != null) {
                if (a.getSleepLmJson() != null && !a.getSleepLmJson().isBlank()) {
                    try {
                        sleepLm = mapper.readValue(a.getSleepLmJson(), SleepLmResponse.class);
                    } catch (Exception ignored) {}
                }
                if (a.getMentaJson() != null && !a.getMentaJson().isBlank()) {
                    try {
                        menta = mapper.readValue(a.getMentaJson(), MentaResponse.class);
                    } catch (Exception ignored) {}
                }
            }
            return new AnalysisResponse(
                    a.getAnalysis(),
                    a.getMoodTrend(),
                    a.getStressTrend(),
                    a.getSleepTrend(),
                    sleepLm,
                    menta,
                    a.getCreatedAt());
        }
    }

    public record SummaryResponse(
            List<EntryResponse> entries,
            AnalysisResponse analysis,
            double averageMood,
            double averageStress,
            double averageEnergy,
            double averageSleep,
            double averageActivity,
            SleepLmResponse sleepLm,
            MentaResponse menta) {}
}
