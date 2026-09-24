package com.healthcompanion.dto;

import com.healthcompanion.dto.WellnessDtos.MentaResponse;
import com.healthcompanion.dto.WellnessDtos.SleepLmResponse;

public record DashboardSummary(
        String userName,
        long foodScans,
        long conversations,
        long wellnessEntries,
        Double currentMood,
        Double averageSleep,
        Double averageActivity,
        SleepLmResponse sleepLm,
        MentaResponse menta) {}
