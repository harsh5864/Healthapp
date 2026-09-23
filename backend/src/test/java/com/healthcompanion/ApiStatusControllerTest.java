package com.healthcompanion;

import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.healthcompanion.controller.ApiStatusController;
import com.healthcompanion.dto.ApiStatusResponse;
import com.healthcompanion.service.AppMetadataService;
import com.healthcompanion.security.JwtService;
import com.healthcompanion.repository.UserRepository;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(ApiStatusController.class)
@AutoConfigureMockMvc(addFilters = false)
class ApiStatusControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private AppMetadataService appMetadataService;

    @MockBean
    private JwtService jwtService;

    @MockBean
    private UserRepository userRepository;

    @Test
    void returnsPublicPlatformStatus() throws Exception {
        given(appMetadataService.getStatus()).willReturn(
                new ApiStatusResponse("available", "AI Health Companion API", "mock", Instant.parse("2026-01-01T00:00:00Z"))
        );

        mockMvc.perform(get("/api/status"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("available"))
                .andExpect(jsonPath("$.aiMode").value("mock"));
    }
}
