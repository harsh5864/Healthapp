package com.healthcompanion.security;
import com.healthcompanion.repository.UserRepository; import jakarta.servlet.*; import jakarta.servlet.http.*; import java.io.IOException; import org.springframework.security.authentication.UsernamePasswordAuthenticationToken; import org.springframework.security.core.authority.SimpleGrantedAuthority; import org.springframework.security.core.context.SecurityContextHolder; import org.springframework.stereotype.Component; import org.springframework.web.filter.OncePerRequestFilter;
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    private final JwtService jwt; private final UserRepository users;
    public JwtAuthenticationFilter(JwtService jwt, UserRepository users){this.jwt=jwt;this.users=users;}
    @Override protected void doFilterInternal(HttpServletRequest request,HttpServletResponse response,FilterChain chain)throws ServletException,IOException { String header=request.getHeader("Authorization"); if(header!=null&&header.startsWith("Bearer ")){String token=header.substring(7); if(jwt.isValid(token)){String email=jwt.extractEmail(token); users.findByEmailIgnoreCase(email).ifPresent(u->SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(u.getEmail(),null,java.util.List.of(new SimpleGrantedAuthority("ROLE_USER")))));}} chain.doFilter(request,response); }
}
