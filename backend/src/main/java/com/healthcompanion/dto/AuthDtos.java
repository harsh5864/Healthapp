package com.healthcompanion.dto;

import jakarta.validation.constraints.*;

public final class AuthDtos {
    private AuthDtos() {}
    public record RegisterRequest(@NotBlank @Size(max=100) String name, @NotBlank @Email @Size(max=190) String email,
                                  @NotBlank @Size(min=8, max=72) String password, @NotBlank String confirmPassword) {}
    public record LoginRequest(@NotBlank @Email String email, @NotBlank String password) {}
    public record UserResponse(Long id, String name, String email) {}
    public record AuthResponse(String token, UserResponse user) {}
    public record ProfileUpdateRequest(@NotBlank @Size(max=100) String name) {}
}
