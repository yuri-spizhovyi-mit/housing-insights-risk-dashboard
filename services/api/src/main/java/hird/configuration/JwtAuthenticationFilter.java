package hird.configuration;

import java.io.IOException;

import hird.service.JwtHelper;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;

import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;

import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.servlet.HandlerExceptionResolver;
import org.springframework.beans.factory.annotation.Qualifier;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final HandlerExceptionResolver exceptionResolver;
    private final UserDetailsService userDetailsService;
    private final JwtHelper jwtHelper;

    public JwtAuthenticationFilter(
            @Qualifier("handlerExceptionResolver") HandlerExceptionResolver exceptionResolver,
            UserDetailsService userDetailsService,
            JwtHelper jwtHelper
    ) {
        this.exceptionResolver = exceptionResolver;
        this.userDetailsService = userDetailsService;
        this.jwtHelper = jwtHelper;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {
        try {
            final String authHeader = request.getHeader("Authorization");

            if (isMissingOrInvalidHeader(authHeader)) {
                filterChain.doFilter(request, response);
                return;
            }

            final String token = extractToken(authHeader);
            final String email = jwtHelper.extractUsername(token);

            if (shouldAuthenticate(email)) {
                authenticateUser(request, token, email);
            }

            filterChain.doFilter(request, response);

        } catch (Exception ex) {
            exceptionResolver.resolveException(request, response, null, ex);
        }
    }

    private boolean isMissingOrInvalidHeader(String header) {
        return header == null || !header.startsWith("Bearer ");
    }

    private String extractToken(String header) {
        return header.substring(7);
    }

    private boolean shouldAuthenticate(String email) {
        Authentication currentAuth = SecurityContextHolder.getContext().getAuthentication();
        return email != null && currentAuth == null;
    }

    private void authenticateUser(HttpServletRequest request, String token, String email) {
        UserDetails userDetails = userDetailsService.loadUserByUsername(email);

        if (!jwtHelper.isValidToken(token, userDetails)) {
            return;
        }

        UsernamePasswordAuthenticationToken authToken =
                new UsernamePasswordAuthenticationToken(
                        userDetails,
                        null,
                        userDetails.getAuthorities()
                );

        authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
        SecurityContextHolder.getContext().setAuthentication(authToken);
    }
}
