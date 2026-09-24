package com.healthcompanion.controller;

import com.healthcompanion.dto.WellnessDtos.*;
import com.healthcompanion.service.WellnessService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/wellness")
public class WellnessController {
    private final WellnessService s;

    public WellnessController(WellnessService s) {
        this.s = s;
    }

    @PostMapping("/check-in")
    public SummaryResponse check(Authentication a, @Valid @RequestBody CheckInRequest r) {
        return s.checkIn(a.getName(), r);
    }

    @GetMapping("/history")
    public List<EntryResponse> history(Authentication a) {
        return s.history(a.getName());
    }

    @GetMapping("/summary")
    public SummaryResponse summary(Authentication a) {
        return s.summary(a.getName());
    }

    @GetMapping("/trends")
    public AnalysisResponse trends(Authentication a) {
        return s.analyze(a.getName());
    }

    @GetMapping("/sleeplm")
    public SleepLmResponse sleepLm(Authentication a) {
        return s.getSleepLm(a.getName());
    }

    @GetMapping("/menta")
    public MentaResponse menta(Authentication a) {
        return s.getMenta(a.getName());
    }
}
