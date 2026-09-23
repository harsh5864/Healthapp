package com.healthcompanion;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.healthcompanion.dto.AuthDtos.RegisterRequest;
import com.healthcompanion.entity.User;
import com.healthcompanion.exception.ApiException;
import com.healthcompanion.repository.UserRepository;
import com.healthcompanion.service.UserService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @Mock
    private UserRepository users;

    @Mock
    private PasswordEncoder encoder;

    private UserService service;

    @BeforeEach
    void setUp() {
        service = new UserService(users, encoder);
    }

    @Test
    void registersNormalizedEmailWithEncodedPassword() {
        RegisterRequest request = new RegisterRequest(
                "  Asha  ", "  ASHA@example.com ", "password123", "password123");
        when(users.existsByEmailIgnoreCase("asha@example.com")).thenReturn(false);
        when(encoder.encode("password123")).thenReturn("encoded-password");
        when(users.save(any(User.class))).thenAnswer(invocation -> invocation.getArgument(0));

        User result = service.register(request);

        assertThat(result.getName()).isEqualTo("Asha");
        assertThat(result.getEmail()).isEqualTo("asha@example.com");
        assertThat(result.getPassword()).isEqualTo("encoded-password");
        verify(encoder).encode("password123");
    }

    @Test
    void rejectsMismatchedPasswordsBeforeWriting() {
        RegisterRequest request = new RegisterRequest(
                "Asha", "asha@example.com", "password123", "different123");

        assertThatThrownBy(() -> service.register(request))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("Passwords do not match");
    }

    @Test
    void rejectsDuplicateEmail() {
        RegisterRequest request = new RegisterRequest(
                "Asha", "asha@example.com", "password123", "password123");
        when(users.existsByEmailIgnoreCase("asha@example.com")).thenReturn(true);

        assertThatThrownBy(() -> service.register(request))
                .isInstanceOf(ApiException.class)
                .hasMessageContaining("already exists");
    }
}
