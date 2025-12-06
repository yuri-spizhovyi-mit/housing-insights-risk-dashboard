package hird.controller;

import hird.dto.RiskGaugeResponse;
import hird.service.RiskGaugeService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;


@RestController
@RequestMapping(path = "/api/v1/risk")
public class RiskGaugeController {
    private final RiskGaugeService riskGaugeService;

    public RiskGaugeController(RiskGaugeService riskGaugeService){
        this.riskGaugeService = riskGaugeService;
    }

    @GetMapping
    public ResponseEntity<RiskGaugeResponse> getRiskGauge(@RequestParam String city){
        RiskGaugeResponse res = riskGaugeService.retrieveRiskGaugeData(city);
        return ResponseEntity.ok(res);
    }
}
