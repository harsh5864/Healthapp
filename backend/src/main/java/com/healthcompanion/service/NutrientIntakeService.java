package com.healthcompanion.service;

import com.healthcompanion.dto.NutrientDtos.*;
import com.healthcompanion.entity.NutrientIntake;
import com.healthcompanion.entity.User;
import com.healthcompanion.exception.ApiException;
import com.healthcompanion.repository.NutrientIntakeRepository;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class NutrientIntakeService {
    private final NutrientIntakeRepository repository;
    private final UserService userService;

    public NutrientIntakeService(NutrientIntakeRepository repository, UserService userService) {
        this.repository = repository;
        this.userService = userService;
    }

    @Transactional
    public IntakeItemResponse logIntake(String email, LogIntakeRequest request) {
        User user = userService.current(email);

        NutrientIntake intake = new NutrientIntake();
        intake.setUser(user);
        intake.setFoodName(request.foodName() != null ? request.foodName().trim() : "Meal Intake");
        
        String mealType = request.mealType() != null && !request.mealType().isBlank()
                ? request.mealType().trim().toUpperCase()
                : "LUNCH";
        intake.setMealType(mealType);

        intake.setCalories(request.calories() != null ? Math.max(0, request.calories()) : 0);
        intake.setProtein(request.protein() != null ? Math.max(0.0, request.protein()) : 0.0);
        intake.setCarbs(request.carbs() != null ? Math.max(0.0, request.carbs()) : 0.0);
        intake.setFat(request.fat() != null ? Math.max(0.0, request.fat()) : 0.0);
        intake.setFiber(request.fiber() != null ? Math.max(0.0, request.fiber()) : 0.0);
        intake.setPortionSize(request.portionSize() != null ? request.portionSize().trim() : null);
        intake.setNotes(request.notes() != null ? request.notes().trim() : null);

        LocalDate date = request.intakeDate() != null ? request.intakeDate() : LocalDate.now();
        intake.setIntakeDate(date);

        NutrientIntake saved = repository.save(intake);

        // Maintain 3-day history rolling window: remove items older than 3 days ago
        try {
            LocalDate cutoff = LocalDate.now().minusDays(3);
            repository.deleteByUserAndIntakeDateBefore(user, cutoff);
        } catch (Exception ignored) {
            // Keep going even if cleanup encountered no-op
        }

        return IntakeItemResponse.from(saved);
    }

    public ThreeDayOverviewDto get3DaySummary(String email) {
        User user = userService.current(email);
        LocalDate today = LocalDate.now();
        LocalDate cutoff = today.minusDays(2); // today, yesterday, 2 days ago = 3 days

        List<NutrientIntake> allRecent = repository.findByUserAndIntakeDateGreaterThanEqualOrderByCreatedAtDesc(user, cutoff);

        Map<LocalDate, List<NutrientIntake>> byDate = allRecent.stream()
                .collect(Collectors.groupingBy(NutrientIntake::getIntakeDate));

        DaySummaryDto day0 = buildDaySummary(today, "Today", byDate.getOrDefault(today, List.of()));
        DaySummaryDto day1 = buildDaySummary(today.minusDays(1), "Yesterday", byDate.getOrDefault(today.minusDays(1), List.of()));
        DaySummaryDto day2 = buildDaySummary(today.minusDays(2), "2 Days Ago", byDate.getOrDefault(today.minusDays(2), List.of()));

        List<DaySummaryDto> history = List.of(day0, day1, day2);

        return new ThreeDayOverviewDto(
                day0,
                history,
                2000,   // Daily Calorie Target
                60.0,   // Daily Protein Target (g)
                250.0,  // Daily Carbs Target (g)
                70.0,   // Daily Fat Target (g)
                30.0    // Daily Fiber Target (g)
        );
    }

    @Transactional
    public void deleteIntake(String email, Long id) {
        User user = userService.current(email);
        NutrientIntake item = repository.findByIdAndUser(id, user)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "INTAKE_NOT_FOUND", "Intake entry not found."));
        repository.delete(item);
    }

    private DaySummaryDto buildDaySummary(LocalDate date, String label, List<NutrientIntake> items) {
        int totalCalories = 0;
        double totalProtein = 0.0;
        double totalCarbs = 0.0;
        double totalFat = 0.0;
        double totalFiber = 0.0;

        List<IntakeItemResponse> responses = new ArrayList<>();
        for (NutrientIntake item : items) {
            totalCalories += item.getCalories() != null ? item.getCalories() : 0;
            totalProtein += item.getProtein() != null ? item.getProtein() : 0.0;
            totalCarbs += item.getCarbs() != null ? item.getCarbs() : 0.0;
            totalFat += item.getFat() != null ? item.getFat() : 0.0;
            totalFiber += item.getFiber() != null ? item.getFiber() : 0.0;
            responses.add(IntakeItemResponse.from(item));
        }

        return new DaySummaryDto(
                date,
                label,
                totalCalories,
                Math.round(totalProtein * 10.0) / 10.0,
                Math.round(totalCarbs * 10.0) / 10.0,
                Math.round(totalFat * 10.0) / 10.0,
                Math.round(totalFiber * 10.0) / 10.0,
                responses
        );
    }
}
