package hird.dto;

public record RegisterUserDto(
        String email,
        String username,
        String password
) {}
