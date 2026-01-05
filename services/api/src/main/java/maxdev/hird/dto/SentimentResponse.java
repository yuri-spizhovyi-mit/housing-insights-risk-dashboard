package maxdev.hird.dto;

import java.util.List;

public record SentimentResponse(
        String city,
        List<SentimentItemResponse> items
) {}

