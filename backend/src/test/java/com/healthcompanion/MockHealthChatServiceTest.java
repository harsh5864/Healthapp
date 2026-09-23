package com.healthcompanion;

import static org.assertj.core.api.Assertions.assertThat;

import com.healthcompanion.ai.MockHealthChatService;
import org.junit.jupiter.api.Test;

class MockHealthChatServiceTest {
    @Test
    void escalatesRedFlagSymptoms() {
        String response = new MockHealthChatService().respond("I have chest pain and difficulty breathing");
        assertThat(response).contains("emergency medical care");
    }

    @Test
    void avoidsDiagnosticLanguageForEverydayQuestion() {
        String response = new MockHealthChatService().respond("What can help with a headache?");
        assertThat(response).contains("professional care").doesNotContain("you have");
    }
}
