package hird.service;

import org.springframework.security.core.userdetails.UserDetails;
import java.util.Map;
import java.util.function.Function;

/**
 * Defines the core operations for working with JWT tokens.
 * The purpose is to make the token-building process explicit,
 * testable, and loosely coupled from the rest of the codebase.
 */
public interface JwtHelper {
    String extractUsername(String token);

    boolean isValidToken(String token, UserDetails userDetails);

    String generateToken(UserDetails userDetails);

    String generateToken(Map<String, Object> extraClaims, UserDetails userDetails);

    <T> T extractClaim(String token, Function<io.jsonwebtoken.Claims, T> resolver);

    long getJwtExpirationMilliseconds();
}
