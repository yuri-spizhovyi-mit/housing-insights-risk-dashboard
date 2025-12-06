package hird.dto;

public record SentimentItemResponse(
        String date,
        String headline,
        String sentiment,
        String url
) {}

