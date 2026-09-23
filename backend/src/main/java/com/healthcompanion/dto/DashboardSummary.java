package com.healthcompanion.dto;
public record DashboardSummary(String userName, long foodScans, long conversations, long wellnessEntries, Double currentMood, Double averageSleep) {}
