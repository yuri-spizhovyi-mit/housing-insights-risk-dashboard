package hird.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.PositiveOrZero;

public record ForecastRequest (
        @NotBlank String city,
        @NotBlank String target,
        @NotBlank String horizon,
        @PositiveOrZero Integer sqftMin,
        @PositiveOrZero Integer sqftMax,
        String propertyType,
        String beds,
        String baths
){}
