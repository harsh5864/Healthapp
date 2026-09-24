package com.healthcompanion.controller;

import com.healthcompanion.dto.DashboardSummary;
import com.healthcompanion.dto.WellnessDtos.MentaResponse;
import com.healthcompanion.dto.WellnessDtos.SleepLmResponse;
import com.healthcompanion.entity.WellnessEntry;
import com.healthcompanion.repository.*;
import com.healthcompanion.service.UserService;
import com.healthcompanion.service.WellnessService;
import java.util.List;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {
    private final UserService users;
    private final FoodScanRepository foods;
    private final ChatConversationRepository chats;
    private final WellnessEntryRepository wellness;
    private final WellnessService wellnessService;

    public DashboardController(
            UserService u,
            FoodScanRepository f,
            ChatConversationRepository c,
            WellnessEntryRepository w,
            WellnessService wellnessService) {
        this.users = u;
        this.foods = f;
        this.chats = c;
        this.wellness = w;
        this.wellnessService = wellnessService;
    }

    @GetMapping("/summary")
    public DashboardSummary summary(Authentication a) {
        var u = users.current(a.getName());
        List<WellnessEntry> e = wellness.findTop30ByUserOrderByCreatedAtDesc(u);
        Double mood = e.isEmpty() ? null : e.get(0).getMood().doubleValue();
        Double sleep = e.isEmpty() ? null : e.stream().mapToDouble(WellnessEntry::getSleepHours).average().orElse(0);
        Double activity = e.isEmpty() ? null : e.stream().mapToDouble(x -> x.getActivity() != null ? x.getActivity() : 5).average().orElse(5);

        SleepLmResponse sleepLm = wellnessService.getSleepLm(a.getName());
        MentaResponse menta = wellnessService.getMenta(a.getName());

        return new DashboardSummary(
                u.getName(),
                foods.countByUser(u),
                chats.countByUser(u),
                wellness.countByUser(u),
                mood,
                sleep,
                activity,
                sleepLm,
                menta);
    }
}
