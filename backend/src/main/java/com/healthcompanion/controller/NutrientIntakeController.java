package com.healthcompanion.controller;

import com.healthcompanion.dto.NutrientDtos.*;
import com.healthcompanion.service.NutrientIntakeService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/nutrients")
public class NutrientIntakeController {
    private final NutrientIntakeService service;

    public NutrientIntakeController(NutrientIntakeService service) {
        this.service = service;
    }

    @PostMapping("/log")
    @ResponseStatus(HttpStatus.CREATED)
    public IntakeItemResponse logIntake(Authentication a, @Valid @RequestBody LogIntakeRequest request) {
        return service.logIntake(a.getName(), request);
    }

    @GetMapping("/3-day-summary")
    public ThreeDayOverviewDto get3DaySummary(Authentication a) {
        return service.get3DaySummary(a.getName());
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteIntake(Authentication a, @PathVariable Long id) {
        service.deleteIntake(a.getName(), id);
    }
}
