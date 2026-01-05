package maxdev.hird.dto;

import java.util.List;

public record ForecastResponse(
        String city,
        String target,
        int horizon,
        List<ForecastPointResponse> data
) {}