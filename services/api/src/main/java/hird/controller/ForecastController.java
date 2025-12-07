package hird.controller;

import hird.dto.ForecastRequest;
import hird.dto.ForecastResponse;
import hird.service.ForecastService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/forecast")
public class ForecastController {
    private final ForecastService forecastService;

    public ForecastController(ForecastService forecastService) {
        this.forecastService = forecastService;
    }

    @GetMapping
    public ResponseEntity<ForecastResponse> getForecast(@Valid @ModelAttribute ForecastRequest forecastRequest) {
        ForecastResponse response = forecastService.retrieveForecast(forecastRequest);
        return ResponseEntity.ok(response);
    }
}
