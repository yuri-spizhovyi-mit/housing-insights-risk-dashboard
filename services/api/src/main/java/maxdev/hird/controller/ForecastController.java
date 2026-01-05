package maxdev.hird.controller;

import jakarta.validation.Valid;
import maxdev.hird.dto.ForecastRequest;
import maxdev.hird.dto.ForecastResponse;
import maxdev.hird.service.ForecastService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/forecast")
public class ForecastController {
    private final ForecastService forecastService;

    public ForecastController(ForecastService forecastService) {
        this.forecastService = forecastService;
    }

    @GetMapping
    public ResponseEntity<ForecastResponse> getForecast(
            @Valid @ModelAttribute ForecastRequest forecastRequest
    ) {
        ForecastResponse response = forecastService.retrieveForecast(forecastRequest);
        return ResponseEntity.ok(response);
    }
}
