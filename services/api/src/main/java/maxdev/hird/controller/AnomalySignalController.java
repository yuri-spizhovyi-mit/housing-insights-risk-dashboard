package maxdev.hird.controller;


import maxdev.hird.dto.AnomalySignalResponse;
import maxdev.hird.service.AnomalySignalService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/anomalies")
public class AnomalySignalController {
    private final AnomalySignalService anomalySignalService;

    public AnomalySignalController(AnomalySignalService anomalySignalService){
        this.anomalySignalService = anomalySignalService;
    }

    @GetMapping
    public ResponseEntity<AnomalySignalResponse> getAnomalies(
            @RequestParam String city,
            @RequestParam String target
    ){
        AnomalySignalResponse anomaly = anomalySignalService.retrieveAnomalies(city, target);
        return ResponseEntity.ok(anomaly);
    }
}
