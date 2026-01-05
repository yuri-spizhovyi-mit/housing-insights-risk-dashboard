package maxdev.hird.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ForecastRequest(
        @NotBlank
        @Size(min=2, max=50)
        String city,

        @NotBlank
        String target,

        @NotBlank
        @Size(min=2, max=3)
        String horizon,

        @NotBlank
        @Size(min=3, max=7)
        String modelName
){}
