package com.healthcompanion.dto;
import com.healthcompanion.entity.*; import jakarta.validation.constraints.*; import java.time.Instant; import java.util.*;
public final class WellnessDtos {
    private WellnessDtos() {}
    public record CheckInRequest(@NotNull @Min(1) @Max(10) Integer mood, @NotNull @Min(1) @Max(10) Integer stress, @NotNull @Min(1) @Max(10) Integer energy, @NotNull @DecimalMin("0") @DecimalMax("24") Double sleepHours, @Size(max=5000) String journalText) {}
    public record EntryResponse(Long id, Integer mood, Integer stress, Integer energy, Double sleepHours, String journalText, Instant createdAt) { public static EntryResponse from(WellnessEntry e) { return new EntryResponse(e.getId(),e.getMood(),e.getStress(),e.getEnergy(),e.getSleepHours(),e.getJournalText(),e.getCreatedAt()); } }
    public record AnalysisResponse(String analysis, String moodTrend, String stressTrend, String sleepTrend, Instant createdAt) { public static AnalysisResponse from(WellnessAnalysis a) { return new AnalysisResponse(a.getAnalysis(),a.getMoodTrend(),a.getStressTrend(),a.getSleepTrend(),a.getCreatedAt()); } }
    public record SummaryResponse(List<EntryResponse> entries, AnalysisResponse analysis, double averageMood, double averageStress, double averageEnergy, double averageSleep) {}
}
