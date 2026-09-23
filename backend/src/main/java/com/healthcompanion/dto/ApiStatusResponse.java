package com.healthcompanion.dto;

import java.time.Instant;

/** Public, non-sensitive readiness data consumed by the frontend connection indicator. */
public record ApiStatusResponse(String status, String application, String aiMode, Instant timestamp) {
}
