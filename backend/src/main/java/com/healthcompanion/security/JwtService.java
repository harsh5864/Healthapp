package com.healthcompanion.security;

import io.jsonwebtoken.*; import io.jsonwebtoken.security.Keys; import java.nio.charset.StandardCharsets; import java.time.Instant; import java.util.Date; import javax.crypto.SecretKey; import org.springframework.beans.factory.annotation.Value; import org.springframework.stereotype.Service;

@Service
public class JwtService {
    private final SecretKey key; private final long expirationMs;
    public JwtService(@Value("${JWT_SECRET:change-this-development-secret-at-least-32-bytes-long}") String secret, @Value("${JWT_EXPIRATION_MS:86400000}") long expirationMs) { if(secret.length()<32) throw new IllegalArgumentException("JWT_SECRET must be at least 32 characters"); this.key=Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8)); this.expirationMs=expirationMs; }
    public String generate(Long userId, String email) { Instant now=Instant.now(); return Jwts.builder().subject(email).claim("userId",userId).issuedAt(Date.from(now)).expiration(new Date(now.toEpochMilli()+expirationMs)).signWith(key).compact(); }
    public String extractEmail(String token) { return parse(token).getPayload().getSubject(); }
    public boolean isValid(String token) { try { parse(token); return true; } catch (JwtException|IllegalArgumentException e) { return false; } }
    private Jws<Claims> parse(String token) { return Jwts.parser().verifyWith(key).build().parseSignedClaims(token); }
}
