package maxdev.hird.service;

import maxdev.hird.domain.exceptions.ResourceNotFoundException;
import maxdev.hird.dto.RiskGaugeIndicator;
import maxdev.hird.dto.RiskGaugeResponse;
import maxdev.hird.model.RiskGauge;
import maxdev.hird.repository.RiskGaugeRepository;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static maxdev.hird.domain.classifier.HousingMarketClassifier.*;

@Service
public class RiskGaugeService {

    private final RiskGaugeRepository repository;

    public RiskGaugeService(RiskGaugeRepository repository) {
        this.repository = repository;
    }


    @Cacheable(
            value = "RISK_CACHE",
            key = "#city.toLowerCase()"
    )
    public RiskGaugeResponse retrieveRiskGaugeData(String city) {
        List<RiskGauge> rows = repository.findByCityIgnoreCaseOrderByPredictDateDesc(city);

        if (rows.isEmpty()) {
            throw new ResourceNotFoundException("No risk data for " + city);
        }

        Map<String, Double> index = toIndex(rows);

        String date = rows.get(0).getPredictDate().toString();
        int score = (int) Math.round(index.getOrDefault("composite_index", 0.0) * 100);

        List<RiskGaugeIndicator> indicators = List.of(
                new RiskGaugeIndicator("Affordability", mapAffordability(index.getOrDefault("affordability", 0.0))),
                new RiskGaugeIndicator("Price-to-Rent", mapPriceToRent(index.getOrDefault("price_to_rent", 0.0))),
                new RiskGaugeIndicator("Inventory", mapInventory(index.getOrDefault("inventory", 0.0)))
        );

        return new RiskGaugeResponse(city, date, score, indicators);
    }

    private Map<String, Double> toIndex(List<RiskGauge> rows) {
        Map<String, Double> index = new HashMap<>();
        rows.forEach(row -> index.put(row.getRiskType(), row.getRiskValue()));

        return index;
    }
}
