package com.healthcompanion.service;
import com.healthcompanion.dto.AuthDtos.*; import com.healthcompanion.entity.User; import com.healthcompanion.exception.ApiException; import com.healthcompanion.repository.UserRepository; import org.springframework.http.HttpStatus; import org.springframework.security.crypto.password.PasswordEncoder; import org.springframework.stereotype.Service; import org.springframework.transaction.annotation.Transactional;
@Service public class UserService {
    private final UserRepository users; private final PasswordEncoder encoder;
    public UserService(UserRepository users,PasswordEncoder encoder){this.users=users;this.encoder=encoder;}
    public User current(String email){return users.findByEmailIgnoreCase(email).orElseThrow(()->new ApiException(HttpStatus.UNAUTHORIZED,"UNAUTHORIZED","Sign in again to continue."));}
    @Transactional public User register(RegisterRequest req){String email=req.email().trim().toLowerCase(); if(!req.password().equals(req.confirmPassword())) throw new ApiException(HttpStatus.BAD_REQUEST,"PASSWORD_MISMATCH","Passwords do not match."); if(users.existsByEmailIgnoreCase(email)) throw new ApiException(HttpStatus.CONFLICT,"EMAIL_EXISTS","An account with this email already exists."); User u=new User();u.setName(req.name().trim());u.setEmail(email);u.setPassword(encoder.encode(req.password()));return users.save(u);}
    public boolean matches(User u,String password){return encoder.matches(password,u.getPassword());}
    @Transactional public User update(User u,ProfileUpdateRequest req){u.setName(req.name().trim());return users.save(u);}
}
