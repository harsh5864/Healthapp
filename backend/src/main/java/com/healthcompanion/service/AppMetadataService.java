package com.healthcompanion.service;

import com.healthcompanion.config.AppProperties;
import com.healthcompanion.dto.ApiStatusResponse;
import java.time.Instant;
import org.springframework.stereotype.Service;

/** Builds the small public payload that verifies frontend-to-backend connectivity. */
@Service
public class AppMetadataService {
    private final AppProperties appProperties;

    public AppMetadataService(AppProperties appProperties) {
        this.appProperties = appProperties;
    }

    public ApiStatusResponse getStatus() {
        return new ApiStatusResponse(
                "available",
                "AI Health Companion API",
                appProperties.getAi().getMode(),
                Instant.now()
        );
    }
}
