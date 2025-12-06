package hird.responses;

public record LoginResponse(
    String login,
    long expiresIn
) {}
