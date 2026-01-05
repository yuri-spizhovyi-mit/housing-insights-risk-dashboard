package maxdev.hird.controller;

import maxdev.hird.dto.RiskGaugeResponse;
import maxdev.hird.service.RiskGaugeService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/risk")
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
