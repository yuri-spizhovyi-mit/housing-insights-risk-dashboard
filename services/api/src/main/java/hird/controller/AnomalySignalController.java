package hird.controller;

import hird.dto.AnomalySignalResponse;
import hird.service.AnomalySignalService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("api/v1/anomalies")
public class AnomalySignalController {

    private final AnomalySignalService service;

    public AnomalySignalController(AnomalySignalService service) {
        this.service = service;
    }

    @GetMapping
    public ResponseEntity<AnomalySignalResponse> getAnomalies(
            @RequestParam String city,
            @RequestParam String target
    ) {
        AnomalySignalResponse anomaly = service.retrieveAnomalies(city, target);
        return ResponseEntity.ok(anomaly);
    }
}
