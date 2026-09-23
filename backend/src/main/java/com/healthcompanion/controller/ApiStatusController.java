package com.healthcompanion.controller;

import com.healthcompanion.dto.ApiStatusResponse;
import com.healthcompanion.service.AppMetadataService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Public Phase 1 endpoint used to prove the React-to-Spring API path. */
@RestController
@RequestMapping("/api")
public class ApiStatusController {
    private final AppMetadataService appMetadataService;

    public ApiStatusController(AppMetadataService appMetadataService) {
        this.appMetadataService = appMetadataService;
    }

    @GetMapping("/status")
    public ResponseEntity<ApiStatusResponse> getStatus() {
        return ResponseEntity.ok(appMetadataService.getStatus());
    }
}
