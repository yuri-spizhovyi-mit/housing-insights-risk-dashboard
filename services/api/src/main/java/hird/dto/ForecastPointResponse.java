package hird.dto;

public record ForecastPointResponse(
        String date,
        double value,
        double lower,
        double upper
) {}
