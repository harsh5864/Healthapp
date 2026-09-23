package com.healthcompanion.ai;

import com.healthcompanion.dto.ChatDtos.MessageResponse;
import java.util.List;

public interface HealthChatService {
    String respond(String message);

    default String respond(String message, List<MessageResponse> history) {
        return respond(message);
    }
}
