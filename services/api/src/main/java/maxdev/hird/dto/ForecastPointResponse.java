package maxdev.hird.dto;

import java.util.Optional;

public record ForecastPointResponse(
        String date,
        Double value,
        Double lower,
        Double upper
) {}

