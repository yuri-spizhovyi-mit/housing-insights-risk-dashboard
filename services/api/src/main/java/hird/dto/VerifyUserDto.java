package hird.dto;

public record VerifyUserDto(
        String email,
        String verificationCode
) {}
