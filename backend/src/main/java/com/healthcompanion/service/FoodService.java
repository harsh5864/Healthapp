package com.healthcompanion.service;

import com.healthcompanion.ai.FoodAnalysisService;
import com.healthcompanion.config.AppProperties;
import com.healthcompanion.dto.FoodDtos.FoodResponse;
import com.healthcompanion.entity.*;
import com.healthcompanion.exception.ApiException;
import com.healthcompanion.repository.FoodScanRepository;
import java.io.IOException;
import java.util.*;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
public class FoodService {
    private final FoodScanRepository scans;
    private final AppProperties props;
    private final UserService users;
    private final FoodAnalysisService ai;

    public FoodService(FoodScanRepository s, AppProperties p, UserService u, FoodAnalysisService ai) {
        this.scans = s;
        this.props = p;
        this.users = u;
        this.ai = ai;
    }

    public FoodResponse analyze(String email, MultipartFile file) {
        return analyze(email, file, "PRODUCE");
    }

    public FoodResponse analyze(String email, MultipartFile file, String scanType) {
        if (file == null || file.isEmpty()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "IMAGE_REQUIRED", "Choose an image to analyze.");
        }
        if (file.getSize() > props.getUpload().getMaxImageBytes()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "IMAGE_TOO_LARGE", "Images must be 8 MB or smaller.");
        }
        String type = file.getContentType() == null ? "" : file.getContentType();
        if (!List.of("image/jpeg", "image/png", "image/webp").contains(type)) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "UNSUPPORTED_IMAGE", "Upload a JPG, PNG or WebP image.");
        }

        String safeScanType = "PRODUCE";
        if (scanType != null) {
            String upper = scanType.toUpperCase();
            if (upper.contains("REAL") || upper.contains("MEAL")) {
                safeScanType = "REAL_FOOD";
            } else if (upper.contains("PACK")) {
                safeScanType = "PACKED_FOOD";
            }
        }

        try {
            User user = users.current(email);
            var result = ai.analyze(file.getOriginalFilename(), file.getBytes(), type, safeScanType);
            FoodScan scan = new FoodScan();
            scan.setUser(user);
            scan.setImageUrl("mock".equalsIgnoreCase(props.getAi().getMode())
                    ? "mock://food/" + UUID.randomUUID()
                    : "ai-service://food/" + UUID.randomUUID());
            scan.setFoodName(result.foodName());
            scan.setFreshnessScore(result.freshnessScore());
            scan.setCondition(result.condition());
            scan.setObservations(result.observations());
            scan.setRecommendation(result.recommendation());
            scan.setScanType(safeScanType);
            scan.setGrade(result.grade());
            scan.setCalories(result.calories());
            scan.setProtein(result.protein());
            scan.setCarbs(result.carbs());
            scan.setFat(result.fat());
            scan.setFiber(result.fiber());
            scan.setPortionSize(result.portionSize());

            return FoodResponse.from(scans.save(scan), "mock".equalsIgnoreCase(props.getAi().getMode()));
        } catch (IOException ex) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "IMAGE_READ_FAILED", "The image could not be read.");
        } catch (IllegalStateException ex) {
            throw new ApiException(HttpStatus.SERVICE_UNAVAILABLE, "AI_UNAVAILABLE", "The food AI service is temporarily unavailable.");
        }
    }

    public List<FoodResponse> history(String email) {
        User u = users.current(email);
        return scans.findTop20ByUserOrderByCreatedAtDesc(u).stream()
                .map(s -> FoodResponse.from(s, "mock".equalsIgnoreCase(props.getAi().getMode())))
                .toList();
    }

    public FoodResponse get(String email, Long id) {
        return FoodResponse.from(
                scans.findByIdAndUser(id, users.current(email))
                        .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "SCAN_NOT_FOUND", "Food scan not found.")),
                "mock".equalsIgnoreCase(props.getAi().getMode()));
    }

    public void delete(String email, Long id) {
        scans.delete(scans.findByIdAndUser(id, users.current(email))
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "SCAN_NOT_FOUND", "Food scan not found.")));
    }
}
